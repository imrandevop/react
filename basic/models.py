from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, localBody, pincode=None):
        if not localBody:
            raise ValueError('Users must have a localBody')
        user = self.model(localBody=localBody, pincode=pincode)
        # Storing pincode as plain text as requested.
        # We are NOT hashing it into the 'password' field.
        user.set_unusable_password() 
        user.save(using=self._db)
        return user

    def create_superuser(self, localBody, pincode=None):
        user = self.create_user(localBody, pincode=pincode)
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    localBody = models.CharField(max_length=255, unique=True)
    pincode = models.CharField(max_length=6)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'localBody'
    REQUIRED_FIELDS = ['pincode']

    def __str__(self):
        return self.localBody

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
