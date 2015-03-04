from core.models import Volume
from rest_framework import serializers
from api.v2.serializers.summaries import (
    ProviderSummarySerializer,
    UserSummarySerializer,
    IdentitySummarySerializer
)


class VolumeSerializer(serializers.HyperlinkedModelSerializer):
    provider = ProviderSummarySerializer(source='instance_source.provider')
    identity = IdentitySummarySerializer(source='instance_source.created_by_identity')
    user = UserSummarySerializer(source='instance_source.created_by')
    start_date = serializers.DateTimeField(source='instance_source.start_date')
    end_date = serializers.DateTimeField(source='instance_source.end_date')
    projects = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Volume
        view_name = 'api_v2:volume-detail'
        fields = ('id', 'url', 'name', 'size', 'user', 'provider', 'identity', 'projects', 'start_date', 'end_date')
