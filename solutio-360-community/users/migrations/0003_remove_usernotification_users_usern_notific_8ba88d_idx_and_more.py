# Generated by Django 5.2.2 on 2025-06-22 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_role_is_reviewer_role_is_staff"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="usernotification",
            name="users_usern_notific_8ba88d_idx",
        ),
        migrations.RemoveIndex(
            model_name="userrole",
            name="users_userr_user_id_acb348_idx",
        ),
        migrations.RemoveIndex(
            model_name="userrole",
            name="users_userr_role_id_3e6b39_idx",
        ),
        migrations.RemoveIndex(
            model_name="usersession",
            name="users_users_last_ac_62f4a2_idx",
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(
                fields=["notification_type"], name="users_usern_notific_e796d4_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(
                fields=["expires_at"], name="users_usern_expires_f233b3_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="userrole",
            index=models.Index(
                fields=["user", "role"], name="users_userr_user_id_595a92_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="userrole",
            index=models.Index(
                fields=["valid_from", "valid_until"],
                name="users_userr_valid_f_12f37c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="usersession",
            index=models.Index(
                fields=["session_key"], name="users_users_session_70af4d_idx"
            ),
        ),
    ]
