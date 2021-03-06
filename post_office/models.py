import sys
import json
from sendgrid.message import SendGridEmailMessage, SendGridEmailMultiAlternatives
from sendgrid.models import Argument, Category
import warnings
from uuid import uuid4
from django.utils.translation import ugettext as _

from collections import namedtuple

from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import models

try:
    from django.utils.encoding import smart_text # For Django >= 1.5
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text

from django.template import Context, Template

from jsonfield import JSONField
import cache
from .settings import get_email_backend
from .validators import validate_email_with_name, validate_template_syntax


PRIORITY = namedtuple('PRIORITY', 'low medium high now')._make(range(4))
STATUS = namedtuple('STATUS', 'sent failed queued')._make(range(3))


# TODO: This will be deprecated, replaced by mail.from_template
class EmailManager(models.Manager):
    def from_template(self, from_email, to_email, template,
                      context={}, priority=PRIORITY.medium):
        warnings.warn(
            "`Email.objects.from_template()` is deprecated and will be removed "
            "in a future relase. Use `post_office.mail.from_template` instead.",
            DeprecationWarning)

        status = None if priority == PRIORITY.now else STATUS.queued
        context = Context(context)
        template_content = Template(template.content)
        template_content_html = Template(template.html_content)
        template_subject = Template(template.subject)
        return Email.objects.create(
            from_email=from_email, to=to_email,
            subject=template_subject.render(context),
            message=template_content.render(context),
            html_message=template_content_html.render(context),
            priority=priority, status=status
        )


class Email(models.Model):
    """
    A model to hold email information.
    """

    PRIORITY_CHOICES = [(PRIORITY.low, 'low'), (PRIORITY.medium, 'medium'),
                        (PRIORITY.high, 'high'), (PRIORITY.now, 'now')]
    STATUS_CHOICES = [(STATUS.sent, 'sent'), (STATUS.failed, 'failed'), (STATUS.queued, 'queued')]

    from_email = models.CharField(max_length=254, validators=[validate_email_with_name])
    to = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)
    html_message = models.TextField(blank=True)
    category = models.CharField(max_length=150, blank=True, null=True, help_text="Primary SendGrid category")
    """
    Emails having 'queued' status will get processed by ``send_all`` command.
    This status field will then be set to ``failed`` or ``sent`` depending on
    whether it's successfully delivered.
    """
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, db_index=True,
                                              blank=True, null=True)
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, blank=True,
                                                null=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    last_updated = models.DateTimeField(db_index=True, auto_now=True)
    scheduled_time = models.DateTimeField(blank=True, null=True, db_index=True)
    headers = JSONField(blank=True, null=True)

    objects = EmailManager()

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return smart_text(self.to,  encoding='utf-8', strings_only=False, errors='strict')

    def email_message(self, connection=None):
        """
        Returns a django ``EmailMessage`` or ``EmailMultiAlternatives`` object
        from a ``Message`` instance, depending on whether html_message is empty.
        """
        subject = smart_text(self.subject)
        # msg = EmailMultiAlternatives(subject, self.message, self.from_email,
        #                              [self.to], connection=connection,
        #                              headers=self.headers)
        msg = EmailMultiAlternatives(subject, self.message, self.from_email,
                                     [self.to], connection=connection,
                                     headers=self.headers)
        if self.html_message:
            msg.attach_alternative(self.html_message, "text/html")

        for attachment in self.attachments.all():
            msg.attach(attachment.name, attachment.file.read())

        # msg = EmailMultiAlternatives(subject, self.message, self.from_email,
        #                              [self.to], connection=connection,
        #                              headers=self.headers)
        msg = SendGridEmailMultiAlternatives(subject, self.message, self.from_email,
                                     [self.to], connection=connection,
                                     headers=self.headers)
        if self.html_message:
            msg.attach_alternative(self.html_message, "text/html")
        if len(self.category) > 0:
            msg.sendgrid_headers.setCategory(self.category)
            msg.sendgrid_headers.setUniqueArgs()
        return msg

    def dispatch(self, connection=None):
        """
        Actually send out the email and log the result
        """
        connection_opened = False
        try:
            if connection is None:
                connection = get_connection(get_email_backend())
                connection.open()
                connection_opened = True

            self.email_sendgrid_message(connection=connection).send()
            status = STATUS.sent
            message = 'Sent'

            if connection_opened:
                connection.close()

        except Exception as err:
            status = STATUS.failed
            message = sys.exc_info()[1]

        self.status = status
        self.save()
        self.logs.create(status=status, message=message)
        return status

    def save(self, *args, **kwargs):
        self.full_clean()
        return super(Email, self).save(*args, **kwargs)


class Log(models.Model):
    """
    A model to record sending email sending activities.
    """

    STATUS_CHOICES = [(STATUS.sent, 'sent'), (STATUS.failed, 'failed')]

    email = models.ForeignKey(Email, editable=False, related_name='logs')
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, db_index=True)
    message = models.TextField()

    class Meta:
        ordering = ('-date',)

    def __unicode__(self):
        return smart_text(self.date,  encoding='utf-8', strings_only=False, errors='strict')


class TemplateVariable(models.Model):
    name = models.CharField(max_length=255, help_text=_("Name of variable to map to"), unique=True)
    static = models.BooleanField(default=False)
    value = models.CharField(max_length=512, null=True, blank=True)
    test_value = models.CharField(max_length=512, default='Testing', null=True)

    # template = models.ManyToManyField(EmailTemplate, null=True, blank=True)

    def __unicode__(self):
        return smart_text(self.name,  encoding='utf-8', strings_only=False, errors='strict')


class EmailCategory(models.Model):
    name = models.CharField(max_length=255, help_text=_("Name of category"))
    # template = models.ManyToManyField(EmailTemplate, null=True, blank=True)

    def __unicode__(self):
        return smart_text(self.name,  encoding='utf-8', strings_only=False, errors='strict')

    class Meta:
        verbose_name_plural = _("Email Categories")
        verbose_name = _("Email Category")


class EmailTemplate(models.Model):
    """
    Model to hold template information from db
    """
    name = models.CharField(max_length=255, help_text=_("Example: 'emails/customers/id/welcome.html'"),
                            validators=[validate_template_syntax])
    description = models.TextField(blank=True,
                                   help_text='Description of this email template.')
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True, )
    html_content = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    variables = models.ManyToManyField(TemplateVariable, 'Variables to look for in template', null=True, blank=True)
    categories = models.ManyToManyField(EmailCategory, help_text=("Categories to include with template."), null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return smart_text(self.name,  encoding='utf-8', strings_only=False, errors='strict')

    def save(self, *args, **kwargs):
        template = super(EmailTemplate, self).save(*args, **kwargs)
        cache.delete(self.name)
        return template


class Attachment(models.Model):
    """
    A model describing an email attachment.
    """
    def get_upload_path(self, filename):
        """Overriding to store the original filename"""
        if not self.name:
            self.name = filename  # set original filename

        filename = '{name}.{ext}'.format(name=uuid4().hex, ext=filename.split('.')[-1])

        return 'post_office_attachments/' + filename

    file = models.FileField(upload_to=get_upload_path)
    name = models.CharField(max_length=255, help_text='The original filename')
    emails = models.ManyToManyField(Email, related_name='attachments')


