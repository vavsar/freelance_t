from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import (PermissionsMixin, UserManager,
                                        _user_has_module_perms, _user_has_perm)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    AUTHOR = 'author'
    EXECUTOR = 'executor'


class User(AbstractBaseUser):
    first_name = models.CharField('First name', max_length=30, blank=True)
    last_name = models.CharField('Last name', max_length=30, blank=True)
    username = models.CharField('Username', max_length=25, unique=True)
    email = models.EmailField('email', unique=True)
    role = models.CharField(
        max_length=15,
        choices=UserRole.choices,
        default=UserRole.EXECUTOR,
    )
    balance = models.DecimalField(default=0, max_digits=10, decimal_places=0,
                                  validators=[MinValueValidator(0)])
    freeze_balance = models.DecimalField(default=0, max_digits=10, decimal_places=0,
                                         validators=[MinValueValidator(0)])
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_(
            'Designates that this user has all permissions without '
            'explicitly assigning them.'
        ),
    )
    username_validator = UnicodeUsernameValidator()
    objects = UserManager()
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    USERNAME_FIELD = 'username'

    @property
    def is_author(self):
        return self.role == UserRole.AUTHOR

    @property
    def is_executor(self):
        return self.role == UserRole.EXECUTOR

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-id']

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def has_perm(self, perm, obj=None):
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_module_perms(self, app_label):
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)
