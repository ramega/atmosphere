from core.models.application import ApplicationScore, ApplicationBookmark
from core.models.credential import Credential
from core.models.group import Group
from core.models.quota import Quota
from core.models.allocation import Allocation
from core.models.identity import Identity
from core.models.instance import Instance
from core.models.instance import InstanceStatusHistory
from core.models.license import License
from core.models.machine import ProviderMachine
from core.models.machine_request import MachineRequest
from core.models.machine_export import MachineExport
from core.models.maintenance import MaintenanceRecord
from core.models.profile import UserProfile
from core.models.project import Project
from core.models.provider import ProviderType
from core.models.request import AllocationRequest, QuotaRequest, StatusType
from core.models.size import Size
from core.models.step import Step
from core.models.tag import Tag
from core.models.user import AtmosphereUser
from core.models.volume import Volume
from core.query import only_current

from rest_framework import serializers

from rest_framework import pagination

from threepio import logger


# Serializers
class ApplicationBookmarkSerializer(serializers.ModelSerializer):
    """
    """
    #TODO:Need to validate provider/identity membership on id change
    type = serializers.SerializerMethodField('get_bookmark_type')
    alias = serializers.SerializerMethodField('get_bookmark_alias')

    def get_bookmark_type(self, bookmark_obj):
        return "Application"

    def get_bookmark_alias(self, bookmark_obj):
        return bookmark_obj.application.uuid

    class Meta:
        model = ApplicationBookmark
        fields = ('type', 'alias')


class ApplicationScoreSerializer(serializers.ModelSerializer):
    """
    """
    #TODO:Need to validate provider/identity membership on id change
    username = serializers.CharField(read_only=True, source='user.username')
    application = serializers.CharField(read_only=True,
                                        source='application.name')
    vote = serializers.CharField(read_only=True, source='get_vote_name')

    class Meta:
        model = ApplicationScore
        fields = ('username', "application", "vote")


class CredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credential
        exclude = ('identity',)


class InstanceSerializer(serializers.ModelSerializer):
    #R/O Fields first!
    alias = serializers.CharField(read_only=True, source='provider_alias')
    alias_hash = serializers.CharField(read_only=True, source='hash_alias')
    application_name = serializers.CharField(
        read_only=True, source='esh_source_name')
    application_uuid = serializers.CharField(
        read_only=True, source='application_uuid')
    #created_by = serializers.CharField(read_only=True, source='creator_name')
    created_by = serializers.SlugRelatedField(slug_field='username',
                                              source='created_by',
                                              read_only=True)
    status = serializers.CharField(read_only=True, source='esh_status')
    fault = serializers.Field(source='esh_fault')
    size_alias = serializers.CharField(read_only=True, source='esh_size')
    machine_alias = serializers.CharField(read_only=True, source='esh_source')
    machine_name = serializers.CharField(read_only=True,
                                         source='esh_source_name')
    machine_alias_hash = serializers.CharField(read_only=True,
                                               source='hash_machine_alias')
    ip_address = serializers.CharField(read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)
    token = serializers.CharField(read_only=True)
    has_shell = serializers.BooleanField(read_only=True, source='shell')
    has_vnc = serializers.BooleanField(read_only=True, source='vnc')
    identity = CleanedIdentitySerializer(source="created_by_identity",
                                         read_only=True)
    #Writeable fields
    name = serializers.CharField()
    tags = TagRelatedField(slug_field='name', source='tags', many=True)
    projects = ProjectsField()
    scripts = BootScriptSerializer(source='scripts', many=True, required=False)

    def __init__(self, *args, **kwargs):
        user = get_context_user(self, kwargs)
        self.request_user = user
        super(InstanceSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Instance
        exclude = ('id', 'source', 'provider_alias',
                   'shell', 'vnc', 'password', 'created_by_identity')


class InstanceHistorySerializer(serializers.ModelSerializer):
    #R/O Fields first!
    alias = serializers.CharField(read_only=True, source='provider_alias')
    alias_hash = serializers.CharField(read_only=True, source='hash_alias')
    created_by = serializers.SlugRelatedField(slug_field='username',
                                              source='created_by',
                                              read_only=True)
    size_alias = serializers.CharField(read_only=True, source='esh_size')
    #NOTE: Now that we have moved to 'source', this can be a bit of a
    # misnomer.. New API should correct this representation.
    machine_alias = serializers.CharField(read_only=True, source='esh_source')
    machine_name = serializers.CharField(read_only=True,
                                         source='esh_source_name')
    machine_alias_hash = serializers.CharField(read_only=True,
                                               source='hash_machine_alias')
    #ENDNOTE
    ip_address = serializers.CharField(read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)
    provider = serializers.CharField(read_only=True, source='provider_name')
    #Writeable fields
    name = serializers.CharField()
    tags = TagRelatedField(slug_field='name', source='tags', many=True)

    class Meta:
        model = Instance
        exclude = ('id', 'source', 'provider_alias',
                   'shell', 'vnc', 'created_by_identity')


class PaginatedInstanceHistorySerializer(pagination.PaginationSerializer):
    """
    Serializes page objects of Instance querysets.
    """
    class Meta:
        object_serializer_class = InstanceHistorySerializer


class PaginatedInstanceSerializer(pagination.PaginationSerializer):
    """
    Serializes page objects of Instance querysets.
    """
    class Meta:
        object_serializer_class = InstanceSerializer


class MachineExportSerializer(serializers.ModelSerializer):
    """
    """
    name = serializers.CharField(source='export_name')
    instance = serializers.SlugRelatedField(slug_field='provider_alias')
    status = serializers.CharField(default="pending")
    disk_format = serializers.CharField(source='export_format')
    owner = serializers.SlugRelatedField(slug_field='username',
                                         source='export_owner')
    file = serializers.CharField(read_only=True, default="",
                                 required=False, source='export_file')

    class Meta:
        model = MachineExport
        fields = ('id', 'instance', 'status', 'name',
                  'owner', 'disk_format', 'file')

class LicenseSerializer(serializers.ModelSerializer):

    created_by = serializers.SlugRelatedField(slug_field='username', read_only=True)
    type = serializers.SlugRelatedField(source='license_type', slug_field='name')

    #TODO: Rename THIS field if it makes more sense for API consumers
    allow_imaging = serializers.BooleanField(source='allow_imaging',
                                             read_only=True)

    class Meta:
        model = License
        exclude = ("license_type",)

class POST_LicenseSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(slug_field='username')
    type = serializers.SlugRelatedField(source='license_type', slug_field='name')
    class Meta:
        model = License
        exclude = ("license_type",)


class MachineRequestSerializer(serializers.ModelSerializer):
    """
    """
    instance = serializers.SlugRelatedField(slug_field='provider_alias')
    status = serializers.CharField(default="pending")
    parent_machine = serializers.SlugRelatedField(slug_field='identifier',
                                                  read_only=True)

    sys = serializers.CharField(default="", source='iplant_sys_files',
                                required=False)
    software = serializers.CharField(default="No software listed",
                                     source='installed_software',
                                     required=False)
    exclude_files = serializers.CharField(default="", required=False)
    shared_with = serializers.CharField(source="access_list", required=False)

    name = serializers.CharField(source='new_machine_name')
    provider = serializers.SlugRelatedField(
        slug_field='uuid', source='new_machine_provider')
    owner = serializers.SlugRelatedField(slug_field='username',
                                         source='new_machine_owner')
    vis = serializers.CharField(source='new_machine_visibility')
    version = serializers.CharField(source='new_machine_version',
            required=False)
    fork = serializers.BooleanField(source='new_machine_forked',
            required=False)
    description = serializers.CharField(source='new_machine_description',
                                        required=False)
    tags = serializers.CharField(source='new_machine_tags', required=False)
    threshold = NewThresholdField(source='new_machine_threshold')
    #TODO: Convert to 'LicenseField' and allow POST of ID instead of
    #      full-object. for additional support for the image creator
    licenses = LicenseSerializer(source='new_machine_licenses.all', many=True)
    new_machine = serializers.SlugRelatedField(slug_field='identifier',
                                               required=False)

    class Meta:
        model = MachineRequest
        fields = ('id', 'instance', 'status', 'name', 'owner', 'provider',
                  'vis', 'description', 'tags', 'sys', 'software',
                  'threshold', 'fork', 'version',
                  'shared_with', 'licenses', 'new_machine')


class MaintenanceRecordSerializer(serializers.ModelSerializer):
    provider_id = serializers.Field(source='provider.uuid')

    class Meta:
        model = MaintenanceRecord
        exclude = ('provider',)


class IdentityDetailSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='creator_name')
    quota = serializers.Field(source='get_quota_dict')
    provider_id = serializers.Field(source='provider.uuid')
    id = serializers.Field(source="uuid")

    class Meta:
        model = Identity
        exclude = ('credentials', 'created_by', 'provider', 'uuid')


class AtmoUserSerializer(serializers.ModelSerializer):
    selected_identity = IdentityRelatedField(source='select_identity')

    def validate_selected_identity(self, attrs, source):
        """
        Check that profile is an identitymember & providermember
        Returns the dict of attrs
        """
        #Short-circut if source (identity) not in attrs
        logger.debug(attrs)
        logger.debug(source)
        if 'selected_identity' not in attrs:
            return attrs
        user = self.object.user
        logger.info("Validating identity for %s" % user)
        selected_identity = attrs['selected_identity']
        logger.debug(selected_identity)
        groups = user.group_set.all()
        import ipdb;ipdb.set_trace()
        for g in groups:
            for id_member in g.identitymembership_set.all():
                if id_member.identity == selected_identity:
                    logger.info("Saving new identity:%s" % selected_identity)
                    user.selected_identity = selected_identity
                    user.save()
                    return attrs
        raise serializers.ValidationError("User is not a member of"
                                          "selected_identity: %s"
                                          % selected_identity)

    class Meta:
        model = AtmosphereUser
        exclude = ('id', 'password')


class ProfileSerializer(serializers.ModelSerializer):
    """
    """
    #TODO:Need to validate provider/identity membership on id change
    username = serializers.CharField(read_only=True, source='user.username')
    email = serializers.CharField(read_only=True, source='user.email')
    groups = serializers.CharField(read_only=True, source='user.groups.all')
    is_staff = serializers.BooleanField(source='user.is_staff')
    is_superuser = serializers.BooleanField(source='user.is_superuser')
    selected_identity = IdentityRelatedField(source='user.select_identity')

    class Meta:
        model = UserProfile
        exclude = ('id',)


class ProviderMachineSerializer(serializers.ModelSerializer):
    #R/O Fields first!
    alias = serializers.CharField(read_only=True, source='identifier')
    alias_hash = serializers.CharField(read_only=True, source='hash_alias')
    created_by = serializers.CharField(
        read_only=True, source='application.created_by.username')
    icon = serializers.CharField(read_only=True, source='icon_url')
    private = serializers.CharField(
        read_only=True, source='application.private')
    architecture = serializers.CharField(read_only=True,
                                         source='esh_architecture')
    ownerid = serializers.CharField(read_only=True, source='esh_ownerid')
    state = serializers.CharField(read_only=True, source='esh_state')
    scores = serializers.SerializerMethodField('get_scores')
    #Writeable fields
    name = serializers.CharField(source='application.name')
    tags = serializers.CharField(source='application.tags.all')
    licenses = LicenseSerializer(source='licenses.all', read_only=True)
    description = serializers.CharField(source='application.description')
    start_date = serializers.CharField(source='start_date')
    end_date = serializers.CharField(source='end_date',
                                     required=False, read_only=True)
    featured = serializers.BooleanField(source='application.featured')
    version = serializers.CharField(source='version')

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop('request_user', None)
        super(ProviderMachineSerializer, self).__init__(*args, **kwargs)

    def get_scores(self, pm):
        app = pm.application
        scores = app.get_scores()
        update_dict = {
            "has_voted": False,
            "vote_cast": None}
        if not self.request_user:
            scores.update(update_dict)
            return scores
        last_vote = ApplicationScore.last_vote(app, self.request_user)
        if last_vote:
            update_dict["has_voted"] = True
            update_dict["vote_cast"] = last_vote.get_vote_name()
        scores.update(update_dict)
        return scores

    class Meta:
        model = ProviderMachine
        exclude = ('id', 'provider', 'application', 'identity')


class PaginatedProviderMachineSerializer(pagination.PaginationSerializer):
    """
    Serializes page objects of ProviderMachine querysets.
    """
    class Meta:
        object_serializer_class = ProviderMachineSerializer


class GroupSerializer(serializers.ModelSerializer):
    identities = serializers.SerializerMethodField('get_identities')

    class Meta:
        model = Group
        exclude = ('id', 'providers')

    def get_identities(self, group):
        identities = group.identities.all()
        return map(lambda i:
                   {"id": i.uuid, "provider_id": i.provider.uuid},
                   identities)


class VolumeSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True, source='get_status')
    attach_data = serializers.Field(source='esh_attach_data')
    #metadata = serializers.Field(source='esh_metadata')
    mount_location = serializers.Field(source='mount_location')
    created_by = serializers.SlugRelatedField(slug_field='username',
                                              source='created_by',
                                              read_only=True)
    provider = serializers.Field(source="provider.uuid")
    identity = CleanedIdentitySerializer(source="created_by_identity")
    projects = ProjectsField()

    def __init__(self, *args, **kwargs):
        user = get_context_user(self, kwargs)
        self.request_user = user
        super(VolumeSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Volume
        exclude = ('id', 'created_by_identity', 'end_date')


class NoProjectSerializer(serializers.ModelSerializer):
    applications = serializers.SerializerMethodField('get_user_applications')
    instances = serializers.SerializerMethodField('get_user_instances')
    volumes = serializers.SerializerMethodField('get_user_volumes')

    def get_user_applications(self, atmo_user):
        return [ApplicationSerializer(
            item,
            context={'request': self.context.get('request')}).data for item in
            atmo_user.application_set.filter(only_current(), projects=None)]

    def get_user_instances(self, atmo_user):
        return [InstanceSerializer(
            item,
            context={'request': self.context.get('request')}).data for item in
            atmo_user.instance_set.filter(only_current(),
                source__provider__active=True,
                projects=None)]

    def get_user_volumes(self, atmo_user):
        return [VolumeSerializer(
            item,
            context={'request': self.context.get('request')}).data for item in
            atmo_user.volume_set().filter(only_current(), 
                provider__active=True, projects=None)]
    class Meta:
        model = AtmosphereUser
        fields = ('applications', 'instances', 'volumes')

class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.Field(source="uuid")
    #Edits to Writable fields..
    owner = serializers.SlugRelatedField(slug_field="name")
    # These fields are READ-ONLY!
    applications = serializers.SerializerMethodField('get_user_applications')
    instances = serializers.SerializerMethodField('get_user_instances')
    volumes = serializers.SerializerMethodField('get_user_volumes')

    def get_user_applications(self, project):
        return [ApplicationSerializer(
            item,
            context={'request': self.context.get('request')}).data for item in
            project.applications.filter(only_current())]

    def get_user_instances(self, project):
        return [InstanceSerializer(
            item,
            context={'request': self.context.get('request')}).data for item in
            project.instances.filter(only_current(),
                source__provider__active=True
                )]

    def get_user_volumes(self, project):
        return [VolumeSerializer(
            item,
            context={'request': self.context.get('request')}).data for item in
            project.volumes.filter(only_current(), provider__active=True)]

    def __init__(self, *args, **kwargs):
        user = get_context_user(self, kwargs)
        super(ProjectSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Project
        exclude = ('uuid', )


class ProviderSizeSerializer(serializers.ModelSerializer):
    occupancy = serializers.CharField(read_only=True, source='esh_occupancy')
    total = serializers.CharField(read_only=True, source='esh_total')
    remaining = serializers.CharField(read_only=True, source='esh_remaining')
    active = serializers.BooleanField(read_only=True, source="active")

    class Meta:
        model = Size
        exclude = ('id', 'start_date', 'end_date')


class StepSerializer(serializers.ModelSerializer):
    alias = serializers.CharField(read_only=True, source='alias')
    name = serializers.CharField()
    script = serializers.CharField()
    exit_code = serializers.IntegerField(read_only=True,
                                         source='exit_code')
    instance_alias = InstanceRelatedField(source='instance.provider_alias')
    created_by = serializers.SlugRelatedField(slug_field='username',
                                              source='created_by',
                                              read_only=True)
    start_date = serializers.DateTimeField(read_only=True)
    end_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Step
        exclude = ('id', 'instance', 'created_by_identity')


class ProviderTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderType


class TagSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field='username')
    description = serializers.CharField(required=False)

    class Meta:
        model = Tag


class InstanceStatusHistorySerializer(serializers.ModelSerializer):
    instance = serializers.SlugRelatedField(slug_field='provider_alias')
    size = serializers.SlugRelatedField(slug_field='alias')

    class Meta:
        model = InstanceStatusHistory


class AllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allocation


class AllocationRequestSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="uuid")
    created_by = serializers.SlugRelatedField(
        slug_field='username', source='created_by', read_only=True)
    status = serializers.SlugRelatedField(
        slug_field='name', source='status', read_only=True)

    class Meta:
        model = AllocationRequest
        exclude = ('uuid', 'membership')


class QuotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quota
        exclude = ("id",)


class QuotaRequestSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="uuid", required=False)
    created_by = serializers.SlugRelatedField(
        slug_field='username', source='created_by',
        queryset=AtmosphereUser.objects.all())
    status = serializers.SlugRelatedField(
        slug_field='name', source='status',
        queryset=StatusType.objects.all())

    class Meta:
        model = QuotaRequest
        exclude = ('uuid', 'membership')


class IdentitySerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source='creator_name')
    credentials = serializers.Field(source='get_credentials')
    id = serializers.Field(source='uuid')
    provider_id = serializers.Field(source='provider_uuid')
    quota = QuotaSerializer(source='get_quota')
    allocation = AllocationSerializer(source='get_allocation')
    membership = serializers.Field(source='get_membership')

    class Meta:
        model = Identity
        fields = ('id', 'created_by', 'provider_id', 'credentials',
                  'membership', 'quota', 'allocation')
