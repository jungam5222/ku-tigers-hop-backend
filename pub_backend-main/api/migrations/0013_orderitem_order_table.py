from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_menu_img'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE api_orderitem
                ADD COLUMN IF NOT EXISTS order_table integer NOT NULL DEFAULT 0;
            """,
            reverse_sql="""
                ALTER TABLE api_orderitem
                DROP COLUMN IF EXISTS order_table;
            """,
        ),
    ]
