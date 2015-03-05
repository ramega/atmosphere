from core.models import Identity
from rest_framework import serializers


class IdentitySummarySerializer(serializers.HyperlinkedModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Identity
        view_name = 'api_v2:identity-detail'
        fields = (
            'id',
            'url',
            'provider',
        )
