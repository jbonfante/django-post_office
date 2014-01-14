# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EmailCategory'
        db.create_table(u'post_office_emailcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'post_office', ['EmailCategory'])

        # Adding model 'TemplateVariable'
        db.create_table(u'post_office_templatevariable', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('static', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=512, null=True, blank=True)),
            ('test_value', self.gf('django.db.models.fields.CharField')(default='Testing', max_length=512, null=True)),
        ))
        db.send_create_signal(u'post_office', ['TemplateVariable'])

        # Adding M2M table for field variables on 'EmailTemplate'
        m2m_table_name = db.shorten_name(u'post_office_emailtemplate_variables')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('emailtemplate', models.ForeignKey(orm[u'post_office.emailtemplate'], null=False)),
            ('templatevariable', models.ForeignKey(orm[u'post_office.templatevariable'], null=False))
        ))
        db.create_unique(m2m_table_name, ['emailtemplate_id', 'templatevariable_id'])

        # Adding M2M table for field categories on 'EmailTemplate'
        m2m_table_name = db.shorten_name(u'post_office_emailtemplate_categories')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('emailtemplate', models.ForeignKey(orm[u'post_office.emailtemplate'], null=False)),
            ('emailcategory', models.ForeignKey(orm[u'post_office.emailcategory'], null=False))
        ))
        db.create_unique(m2m_table_name, ['emailtemplate_id', 'emailcategory_id'])

        # Adding field 'Email.category'
        db.add_column(u'post_office_email', 'category',
                      self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'EmailCategory'
        db.delete_table(u'post_office_emailcategory')

        # Deleting model 'TemplateVariable'
        db.delete_table(u'post_office_templatevariable')

        # Removing M2M table for field variables on 'EmailTemplate'
        db.delete_table(db.shorten_name(u'post_office_emailtemplate_variables'))

        # Removing M2M table for field categories on 'EmailTemplate'
        db.delete_table(db.shorten_name(u'post_office_emailtemplate_categories'))

        # Deleting field 'Email.category'
        db.delete_column(u'post_office_email', 'category')


    models = {
        u'post_office.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'emails': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'attachments'", 'symmetrical': 'False', 'to': u"orm['post_office.Email']"}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'post_office.email': {
            'Meta': {'ordering': "('-created',)", 'object_name': 'Email'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'from_email': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'headers': ('jsonfield.fields.JSONField', [], {'null': 'True', 'blank': 'True'}),
            'html_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'scheduled_time': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'to': ('django.db.models.fields.EmailField', [], {'max_length': '254'})
        },
        u'post_office.emailcategory': {
            'Meta': {'object_name': 'EmailCategory'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'post_office.emailtemplate': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EmailTemplate'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['post_office.EmailCategory']", 'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'html_content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'variables': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['post_office.TemplateVariable']", 'null': 'True', 'blank': 'True'})
        },
        u'post_office.log': {
            'Meta': {'ordering': "('-date',)", 'object_name': 'Log'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'logs'", 'to': u"orm['post_office.Email']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        u'post_office.templatevariable': {
            'Meta': {'object_name': 'TemplateVariable'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'static': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'test_value': ('django.db.models.fields.CharField', [], {'default': "'Testing'", 'max_length': '512', 'null': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['post_office']