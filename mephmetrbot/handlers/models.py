from tortoise import fields, models

class Users(models.Model):
    id = fields.BigIntField(pk=True)
    drug_count = fields.BigIntField(default=0)
    vip = fields.IntField(default=0)
    last_use_time = fields.DatetimeField(null=True)
    is_admin = fields.BooleanField(default=False)
    is_tester = fields.BooleanField(default=False)
    is_banned = fields.BooleanField(default=False)
    last_casino = fields.DatetimeField(null=True)
    bonus = fields.BooleanField(default=False)
    vip_bonus = fields.DateField(null=True)
    last_find = fields.DatetimeField(null=True)
    clan_member = fields.IntField(null=True)
    game_count = fields.IntField(default=0)
    last_game_day = fields.DateField(null=True)
    clan_invite = fields.IntField(null=True)
    balance = fields.BigIntField(default=0)
    last_work = fields.DatetimeField(null=True)
    ban_end_time = fields.DatetimeField(null=True)
    ban_reason = fields.CharField(max_length=255, null=True)
    invite_timestamp = fields.DatetimeField(null=True)

class Chats(models.Model):
    chat_id = fields.BigIntField(pk=True)
    is_ads_enable = fields.BooleanField(default=True)

class Clans(models.Model):
    clan_id = fields.IntField(null=True)
    clan_name = fields.CharField(max_length=255)
    clan_owner_id = fields.BigIntField()
    clan_balance = fields.IntField(default=0)

class Invoices(models.Model):
    invoice_id = fields.BigIntField(pk=True)
    status = fields.CharField(max_length=255)