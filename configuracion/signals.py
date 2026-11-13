from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ConfiguracionSistema


@receiver(post_save, sender=ConfiguracionSistema)
def invalidar_cache_post_save(sender, instance, **kwargs):
    cache.delete(f"configsys:{instance.clave}")


@receiver(post_delete, sender=ConfiguracionSistema)
def invalidar_cache_post_delete(sender, instance, **kwargs):
    cache.delete(f"configsys:{instance.clave}")
