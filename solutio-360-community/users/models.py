from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class User(AbstractUser):
    """
    Özel kullanıcı modeli - Django'nun AbstractUser'ından genişletilmiş.

    Sistem için özelleştirilmiş kullanıcı modeli.
    Ek alanlar ve işlevsellik içerir:
    - Telefon numarası
    - Avatar resmi
    - Departman bilgisi
    - Çift faktörlü kimlik doğrulama
    - Bildirim tercihleri

    Attributes:
        phone_number: Telefon numarası (uluslararası format)
        avatar: Profil resmi
        department: Kullanıcının departmanı
        position: İş pozisyonu
        employee_id: Personel numarası
        is_verified: Email doğrulanmış mı?
        two_factor_enabled: 2FA aktif mi?
        notification_preferences: Bildirim ayarları
    """

    # Telefon numarası doğrulama regex'i
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$",
        message=_(
            "Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        ),
    )

    # Telefon numarası - uluslararası format
    phone_number = models.CharField(
        _("phone number"), validators=[phone_regex], max_length=17, blank=True
    )

    # Kullanıcı avatar resmi
    avatar = models.ImageField(
        _("avatar"), upload_to="users/avatars/%Y/%m/", null=True, blank=True
    )

    # Kullanıcının departmanı - foreign key
    department = models.ForeignKey(
        "Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("department"),
    )

    # İş pozisyonu
    position = models.CharField(_("position"), max_length=100, blank=True)

    # Personel numarası - benzersiz
    employee_id = models.CharField(
        _("employee ID"), max_length=50, unique=True, null=True, blank=True
    )

    # Email doğrulanmış mı?
    is_verified = models.BooleanField(_("is verified"), default=False)

    # Email doğrulama token'ı
    verification_token = models.CharField(
        _("verification token"), max_length=100, null=True, blank=True
    )

    # Son giriş IP adresi
    last_login_ip = models.GenericIPAddressField(
        _("last login IP"), null=True, blank=True
    )

    # İki faktörlü kimlik doğrulama aktif mi?
    two_factor_enabled = models.BooleanField(_("two factor enabled"), default=False)

    # 2FA için gizli anahtar
    two_factor_secret = models.CharField(
        _("two factor secret"), max_length=32, null=True, blank=True
    )

    # Bildirim tercihleri - JSON formatında
    notification_preferences = models.JSONField(
        _("notification preferences"), default=dict
    )

    # Tercih edilen dil
    language_preference = models.CharField(
        _("language preference"), max_length=10, default="tr"
    )

    # Saat dilimi
    timezone = models.CharField(_("timezone"), max_length=50, default="Europe/Istanbul")

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["username"]
        indexes = [
            # Performans için indexler
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["employee_id"]),
        ]

    def __str__(self):
        """
        Kullanıcının string temsili.

        Returns:
            str: Tam ad veya kullanıcı adı
        """
        return self.get_full_name() or self.username

    def get_absolute_url(self):
        """
        Kullanıcının detay sayfası URL'si.

        Returns:
            str: Kullanıcı detay URL'si
        """
        from django.urls import reverse

        return reverse("users:user-detail", args=[str(self.id)])

    @property
    def full_name(self):
        """
        Kullanıcının tam adı.

        Returns:
            str: Ad soyad veya kullanıcı adı
        """
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_personnel(self):
        """
        Kullanıcının personel (staff veya reviewer) olup olmadığını kontrol eder.

        Bu özellik rol tabanlı yetkilendirme için kullanılır.

        Returns:
            bool: Personel ise True, değilse False
        """
        return (
            self.user_roles.filter(role__is_staff=True).exists()
            or self.user_roles.filter(role__is_reviewer=True).exists()
        )


class UserProfile(models.Model):
    """
    Kullanıcı profil detayları modeli.

    User modelini genişletir ve ek kişisel bilgileri saklar.
    One-to-One ilişki ile User modeline bağlıdır.

    Bu model kullanıcılar hakkında daha detaylı bilgi saklar:
    - Kişisel bilgiler (doğum tarihi, cinsiyet, adres)
    - İletişim bilgileri (alternatif email, telefon)
    - Sosyal medya hesapları
    - Kullanıcı tercihleri (dil, tema, saat dilimi)
    - İstatistikler (profil görüntülenme sayısı)
    """

    # User modeli ile one-to-one ilişki
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Kullanıcı"),
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Kişisel Bilgiler
    birth_date = models.DateField(_("Doğum Tarihi"), null=True, blank=True)

    gender = models.CharField(
        _("Cinsiyet"),
        max_length=10,
        choices=[("M", "Erkek"), ("F", "Kadın"), ("O", "Diğer")],
        blank=True,
    )

    address = models.TextField(_("Adres"), blank=True)
    city = models.CharField(_("Şehir"), max_length=100, blank=True)
    country = models.CharField(_("Ülke"), max_length=100, blank=True)

    # İletişim Bilgileri
    alternative_email = models.EmailField(_("Alternatif E-posta"), blank=True)
    alternative_phone = models.CharField(
        _("Alternatif Telefon"), max_length=20, blank=True
    )

    # Sosyal Medya Hesapları
    linkedin = models.URLField(_("LinkedIn"), blank=True)
    twitter = models.URLField(_("Twitter"), blank=True)
    facebook = models.URLField(_("Facebook"), blank=True)
    instagram = models.URLField(_("Instagram"), blank=True)

    # Kullanıcı Tercihleri
    language = models.CharField(
        _("Dil"),
        max_length=10,
        choices=[("tr", "Türkçe"), ("en", "English")],
        default="tr",
    )

    timezone = models.CharField(
        _("Saat Dilimi"), max_length=50, default="Europe/Istanbul"
    )

    theme = models.CharField(
        _("Tema"),
        max_length=20,
        choices=[("light", "Açık"), ("dark", "Koyu"), ("system", "Sistem")],
        default="system",
    )

    # İstatistikler
    profile_views = models.PositiveIntegerField(_("Profil Görüntülenme"), default=0)
    last_profile_update = models.DateTimeField(
        _("Son Profil Güncelleme"), auto_now=True
    )

    class Meta:
        verbose_name = _("Kullanıcı Profili")
        verbose_name_plural = _("Kullanıcı Profilleri")

    def __str__(self):
        """
        Profil string temsili.

        Returns:
            str: Kullanıcı adı + "Profili"
        """
        return f"{self.user.get_full_name()} Profili"


class Department(BaseModel):
    """
    Departman modeli.

    Organizasyonel yapıyı temsil eder.
    Hiyerarşik yapı destekler (alt departmanlar).

    Attributes:
        name: Departman adı
        code: Departman kodu (benzersiz)
        description: Açıklama
        parent: Üst departman (hiyerarşi için)
        manager: Departman yöneticisi
        contact_info: İletişim bilgileri
    """

    # Departman adı
    name = models.CharField(_("name"), max_length=100)

    # Departman kodu - benzersiz
    code = models.CharField(_("code"), max_length=20, unique=True)

    # Açıklama
    description = models.TextField(_("description"), blank=True)

    # Üst departman - hiyerarşi için
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("parent department"),
    )

    # Departman yöneticisi
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        verbose_name=_("manager"),
    )

    # İletişim bilgileri
    email = models.EmailField(_("email"), blank=True)
    phone = models.CharField(_("phone"), max_length=20, blank=True)
    address = models.TextField(_("address"), blank=True)

    # Sıralama
    order = models.PositiveIntegerField(_("order"), default=0)

    # Aktif mi?
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["parent"]),
        ]

    def __str__(self):
        """
        Departmanın string temsili.

        Returns:
            str: Departman adı
        """
        return self.name

    def get_absolute_url(self):
        """
        Departman detay sayfası URL'si.

        Returns:
            str: Departman detay URL'si
        """
        from django.urls import reverse

        return reverse("users:department-detail", args=[str(self.id)])


class Role(BaseModel):
    """
    Rol modeli.

    Kullanıcı rollerini ve izinlerini tanımlar.
    Sistem rolü veya departman rolü olabilir.

    Attributes:
        name: Rol adı
        code: Rol kodu (benzersiz)
        description: Açıklama
        permissions: İzinler (JSON formatında)
        is_system: Sistem rolü mü?
        department: Hangi departman için
        is_staff: Personel rolü mü?
        is_reviewer: İnceleme yetkilisi mi?
    """

    # Rol adı
    name = models.CharField(_("name"), max_length=100)

    # Rol kodu - benzersiz
    code = models.CharField(_("code"), max_length=50, unique=True)

    # Açıklama
    description = models.TextField(_("description"), blank=True)

    # İzinler - JSON formatında
    permissions = models.JSONField(_("permissions"), default=list)

    # Sistem rolü mü?
    is_system = models.BooleanField(_("is system"), default=False)

    # Hangi departman için
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="roles",
        verbose_name=_("department"),
    )

    # Personel rolü mü?
    is_staff = models.BooleanField(_("Personel Rolü"), default=False)

    # İnceleme yetkilisi mi?
    is_reviewer = models.BooleanField(_("İnceleme Yetkilisi"), default=False)

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        """
        Rolün string temsili.

        Returns:
            str: Rol adı
        """
        return self.name

    def get_absolute_url(self):
        """
        Rol detay sayfası URL'si.

        Returns:
            str: Rol detay URL'si
        """
        from django.urls import reverse

        return reverse("users:role-detail", args=[str(self.id)])


class UserRole(BaseModel):
    """
    Kullanıcı-Rol atama modeli.

    Kullanıcıların hangi rollerde olduğunu belirler.
    Bir kullanıcının birden fazla rolü olabilir.
    Geçerlilik tarihi aralığı belirlenebilir.

    Attributes:
        user: Kullanıcı
        role: Rol
        department: Departman
        is_primary: Birincil rol mü?
        valid_from: Geçerlilik başlangıcı
        valid_until: Geçerlilik bitişi
    """

    # Kullanıcı
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name=_("user"),
    )

    # Rol
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name=_("role"),
    )

    # Departman
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name=_("department"),
    )

    # Birincil rol mü?
    is_primary = models.BooleanField(_("is primary"), default=False)

    # Geçerlilik tarihleri
    valid_from = models.DateTimeField(_("valid from"), null=True, blank=True)
    valid_until = models.DateTimeField(_("valid until"), null=True, blank=True)

    class Meta:
        verbose_name = _("user role")
        verbose_name_plural = _("user roles")
        unique_together = ["user", "role", "department"]
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["valid_from", "valid_until"]),
        ]

    def __str__(self):
        """
        Kullanıcı-rol atamasının string temsili.

        Returns:
            str: Kullanıcı - Rol - Departman
        """
        return f"{self.user.username} - {self.role.name} - {self.department.name}"


class UserSession(BaseModel):
    """
    Kullanıcı oturum takip modeli.

    Aktif kullanıcı oturumlarını takip eder.
    Güvenlik ve audit için kullanılır.

    Attributes:
        user: Kullanıcı
        session_key: Django session anahtarı
        ip_address: IP adresi
        user_agent: Browser bilgisi
        last_activity: Son aktivite zamanı
        is_active: Oturum aktif mi?
    """

    # Kullanıcı
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sessions", verbose_name=_("user")
    )

    # Django session anahtarı
    session_key = models.CharField(_("session key"), max_length=40, unique=True)

    # IP adresi
    ip_address = models.GenericIPAddressField(_("IP address"))

    # Browser bilgisi
    user_agent = models.TextField(_("user agent"))

    # Son aktivite zamanı
    last_activity = models.DateTimeField(_("last activity"), auto_now=True)

    # Oturum aktif mi?
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        verbose_name = _("user session")
        verbose_name_plural = _("user sessions")
        ordering = ["-last_activity"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self):
        """
        Oturumun string temsili.

        Returns:
            str: Kullanıcı - IP - Son aktivite
        """
        return f"{self.user.username} - {self.ip_address} - {self.last_activity}"


class UserActivity(BaseModel):
    """
    Kullanıcı aktivite takip modeli.

    Kullanıcıların sistemdeki aktivitelerini loglar.
    Audit trail ve güvenlik için kritik.

    Attributes:
        user: Kullanıcı
        action: Yapılan işlem
        ip_address: IP adresi
        user_agent: Browser bilgisi
        details: İşlem detayları (JSON)
    """

    # Yapılabilecek işlem türleri
    ACTION_CHOICES = (
        ("LOGIN", _("Login")),
        ("LOGOUT", _("Logout")),
        ("PASSWORD_CHANGE", _("Password Change")),
        ("PROFILE_UPDATE", _("Profile Update")),
        ("ROLE_CHANGE", _("Role Change")),
        ("PERMISSION_CHANGE", _("Permission Change")),
        ("OTHER", _("Other")),
    )

    # Kullanıcı
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name=_("user"),
    )

    # Yapılan işlem
    action = models.CharField(_("action"), max_length=20, choices=ACTION_CHOICES)

    # IP adresi
    ip_address = models.GenericIPAddressField(_("IP address"))

    # Browser bilgisi
    user_agent = models.TextField(_("user agent"))

    # İşlem detayları - JSON formatında
    details = models.JSONField(_("details"), default=dict)

    class Meta:
        verbose_name = _("user activity")
        verbose_name_plural = _("user activities")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """
        Aktivitenin string temsili.

        Returns:
            str: Kullanıcı - İşlem - Tarih
        """
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at}"


class UserNotification(BaseModel):
    """
    Kullanıcı bildirim modeli.

    Kullanıcılara gönderilen bildirimleri saklar.
    Farklı türlerde bildirimler desteklenir.

    Attributes:
        user: Bildirim alacak kullanıcı
        notification_type: Bildirim türü
        title: Bildirim başlığı
        message: Bildirim mesajı
        is_read: Okundu mu?
        read_at: Okunma zamanı
        data: Ek veri (JSON)
        priority: Öncelik seviyesi
        expires_at: Son geçerlilik
    """

    # Bildirim türleri
    NOTIFICATION_TYPES = (
        ("SYSTEM", _("System")),
        ("COMPLAINT", _("Complaint")),
        ("ROLE", _("Role")),
        ("DEPARTMENT", _("Department")),
        ("OTHER", _("Other")),
    )

    # Bildirim alacak kullanıcı
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("user"),
    )

    # Bildirim türü
    notification_type = models.CharField(
        _("notification type"), max_length=20, choices=NOTIFICATION_TYPES
    )

    # Bildirim başlığı
    title = models.CharField(_("title"), max_length=200)

    # Bildirim mesajı
    message = models.TextField(_("message"))

    # Okundu mu?
    is_read = models.BooleanField(_("is read"), default=False)

    # Okunma zamanı
    read_at = models.DateTimeField(_("read at"), null=True, blank=True)

    # Ek veri - JSON formatında
    data = models.JSONField(_("data"), default=dict)

    # Öncelik seviyesi (0-10 arası)
    priority = models.PositiveSmallIntegerField(_("priority"), default=0)

    # Son geçerlilik tarihi
    expires_at = models.DateTimeField(_("expires at"), null=True, blank=True)

    class Meta:
        verbose_name = _("user notification")
        verbose_name_plural = _("user notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["notification_type"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        """
        Bildirimin string temsili.

        Returns:
            str: Kullanıcı - Başlık
        """
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        """
        Bildirimi okundu olarak işaretle.

        Okunma zamanını şu anki zaman olarak ayarlar.
        """
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])


# Signals
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Yeni kullanıcı oluşturulduğunda otomatik profil oluştur.

    Args:
        sender: User modeli
        instance: Oluşturulan kullanıcı instance'ı
        created: Yeni oluşturuldu mu?
        **kwargs: Ek parametreler
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Kullanıcı kaydedildiğinde profili de kaydet.

    Args:
        sender: User modeli
        instance: Kullanıcı instance'ı
        **kwargs: Ek parametreler
    """
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
