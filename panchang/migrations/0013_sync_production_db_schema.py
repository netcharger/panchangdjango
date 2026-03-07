# Generated manually to patch missing SQL columns in production DB since Django State faked them
from django.db import migrations, connection

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table in MySQL"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            AND COLUMN_NAME = %s
        """, [table_name, column_name])
        return cursor.fetchone()[0] > 0

def sync_schema(apps, schema_editor):
    """Add only the missing MySQL columns/tables without touching Django's migration history."""
    table_name = 'panchang_data'
    
    # These match the CharField(max_length=50, null=True, blank=True) added in 0009
    columns_to_add = [
        'sunrise', 'sunset', 'moonrise', 'moonset',
        'abhijit_muhurtham', 'amrita_kalam', 'brahma_muhurtham',
        'pratah_sandhya', 'vijaya_muhurtham', 'godhuli_muhurtham',
        'sayam_sandhya', 'nishita_muhurtham'
    ]
    
    with connection.cursor() as cursor:
        # 1. Add missing fields if they don't exist
        for col in columns_to_add:
            if not check_column_exists(table_name, col):
                cursor.execute(f"ALTER TABLE `{table_name}` ADD COLUMN `{col}` VARCHAR(50) NULL")
                
        # 2. Cleanup old dropped fields if they still exist (from 0010/0011)
        columns_to_remove = ['day', 'gulika_kalam', 'rahu_kalam', 'yamagandam']
        for col in columns_to_remove:
            if check_column_exists(table_name, col):
                cursor.execute(f"ALTER TABLE `{table_name}` DROP COLUMN `{col}`")
                
        # `festivals` was added then dropped, so drop if exists
        if check_column_exists(table_name, 'festivals'):
            cursor.execute(f"ALTER TABLE `{table_name}` DROP COLUMN `festivals`")
                
        # 3. Ensure the daily festivals table exists just in case (from 0011/0012)
        # Using IF NOT EXISTS so it's perfectly safe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `panchang_data_daily_festivals` (
                `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
                `festival_name` varchar(200) COLLATE utf8mb4_general_ci NOT NULL,
                `festival_reference_id` bigint NULL,
                `panchang_data_id` bigint NOT NULL,
                CONSTRAINT `panchang_data_dai_festival_reference_id_abcdef12_fk_festivals_id` FOREIGN KEY (`festival_reference_id`) REFERENCES `festivals` (`id`),
                CONSTRAINT `panchang_data_dai_panchang_data_id_12345678_fk_panchang_data_id` FOREIGN KEY (`panchang_data_id`) REFERENCES `panchang_data` (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """)

def reverse_sync(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('panchang', '0012_alter_panchangdailyfestival_table'),
    ]

    operations = [
        migrations.RunPython(sync_schema, reverse_sync),
    ]
