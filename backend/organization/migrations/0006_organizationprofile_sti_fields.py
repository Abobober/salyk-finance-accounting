from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0005_remove_organizationprofile_organization_tax_period_state_valid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationprofile',
            name='contact_phone',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='organizationprofile',
            name='inn',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='organizationprofile',
            name='tax_authority_code',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='organizationprofile',
            name='tax_authority_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='organizationprofile',
            name='taxpayer_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
