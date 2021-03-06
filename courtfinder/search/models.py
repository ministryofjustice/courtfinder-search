from urllib.parse import unquote
from django.db import models
from django.utils import timezone


class Court(models.Model):
    admin_id = models.IntegerField(null=True, default=None)
    name = models.CharField(max_length=255)
    name_cy = models.CharField(max_length=255, null=True, default=None, blank=True)
    slug = models.SlugField(max_length=255)
    displayed = models.BooleanField(default=False)
    lat = models.FloatField(null=True)
    lon = models.FloatField(null=True)
    number = models.IntegerField(null=True, blank=True) #Crown court location number
    parking = models.ForeignKey('ParkingInfo', models.CASCADE)
    alert = models.CharField(max_length=250, null=True, default=None, blank=True)
    alert_cy = models.CharField(max_length=250, null=True, default=None, blank=True)
    directions = models.CharField(max_length=4096, null=True, default=None, blank=True)
    directions_cy = models.CharField(max_length=4096, null=True, default=None, blank=True)
    image_file = models.CharField(max_length=255, null=True, default=None)
    areas_of_law = models.ManyToManyField('AreaOfLaw', through='CourtAreaOfLaw')
    emails = models.ManyToManyField('Email', through='CourtEmail')
    attributes = models.ManyToManyField('CourtAttributeType', through='CourtAttribute')
    addresses = models.ManyToManyField('AddressType', through='CourtAddress')
    court_types = models.ManyToManyField('CourtType', through='CourtCourtType')
    facilities = models.ManyToManyField('Facility', through='CourtFacility')
    opening_times = models.ManyToManyField('OpeningTime', through='CourtOpeningTime')
    contacts = models.ManyToManyField('Contact', through='CourtContact')
    cci_code = models.IntegerField(null=True, blank=True) #County court location number
    magistrate_code = models.IntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, default=None)
    created_at = models.DateTimeField(null=True, default=None)
    info = models.TextField(null=True, blank=True)
    info_cy = models.TextField(null=True, blank=True)
    hide_aols = models.BooleanField(null=False, default=False)
    info_leaflet = models.CharField(max_length=2500, null=True, default=None, blank=True)
    info_leaflet_cy = models.CharField(max_length=2500, null=True, default=None, blank=True)
    defence_leaflet = models.CharField(max_length=2500, null=True, default=None, blank=True)
    defence_leaflet_cy = models.CharField(max_length=2500, null=True, default=None, blank=True)
    prosecution_leaflet = models.CharField(max_length=2500, null=True, default=None, blank=True)
    prosecution_leaflet_cy = models.CharField(max_length=2500, null=True, default=None, blank=True)
    juror_leaflet = models.CharField(max_length=2500, null=True, default=None, blank=True)
    welsh_enabled = models.BooleanField(default=False)
    gbs = models.TextField(null=True, blank=True)

    def postcodes_covered(self):
        return CourtPostcode.objects.filter(court=self)

    def __str__(self):
        return self.name

    def update_timestamp(self):
        #todo move into save after migration
        self.updated_at = timezone.now()
        self.save()

    def primary_address(self):
        try:
            return CourtAddress.objects.filter(court=self).order_by('pk').first()
        except CourtAddress.DoesNotExist:
            return None


class CourtAttributeType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CourtAttribute(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    attribute_type = models.ForeignKey(CourtAttributeType, models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return "%s.%s = %s" % (self.court.name, self.attribute_type.name, self.value)


class CourtPostcode(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    postcode = models.CharField(max_length=250)

    def __str__(self):
        return "%s covers %s" % (self.court.name, self.postcode)


class AreaOfLaw(models.Model):
    name = models.CharField(max_length=255)
    alt_name = models.CharField(max_length=255, blank=True, null=True)
    alt_name_cy = models.CharField(max_length=255, blank=True, null=True)
    external_link = models.CharField(null=True, max_length=2048)
    external_link_cy = models.CharField(blank=True, null=True, default=None, max_length=2048)
    external_link_desc = models.CharField(null=True, max_length=255)
    external_link_desc_cy = models.CharField(blank=True, null=True, default=None, max_length=255)

    def display_url(self):
        return unquote(self.external_link)

    def display_url_cy(self):
        return unquote(self.external_link_cy) if self.external_link_cy else self.display_url()

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)


class Facility(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=4096, null=True, blank=True)
    description_cy = models.CharField(max_length=4096, null=True, blank=True)
    image = models.CharField(max_length=255)
    image_description = models.CharField(max_length=255)
    image_file_path = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "%s: %s" % (self.name, self.description)

    @property
    def order_label(self):
        return "%s" % self.name


class OpeningTime(models.Model):
    type = models.CharField(null=True, max_length=255, default=None)
    hours = models.CharField(null=True, max_length=255, default=None)

    def __str__(self):
        if self.hours:
            return "%s: %s" % (self.type, self.hours)
        else:
            return "%s" % self.type

    @property
    def order_label(self):
        return "%s" % self.type


class LocalAuthority(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name


class CourtLocalAuthorityAreaOfLaw(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    area_of_law = models.ForeignKey(AreaOfLaw, models.CASCADE)
    local_authority = models.ForeignKey(LocalAuthority, models.CASCADE)

    def __str__(self):
        return "%s covers %s for %s" % (self.court.name,
                                        self.local_authority.name,
                                        self.area_of_law.name)


class CourtFacility(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    facility = models.ForeignKey(Facility, models.CASCADE)

    def __str__(self):
        return "%s has facility %s" % (self.court.name, self.facility)


class CourtOpeningTime(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    opening_time = models.ForeignKey(OpeningTime, models.CASCADE)
    sort = models.IntegerField(default=0)

    def __str__(self):
        return "%s has facility %s" % (self.court.name, self.opening_time)


class CourtAreaOfLaw(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    area_of_law = models.ForeignKey(AreaOfLaw, models.CASCADE)
    single_point_of_entry = models.BooleanField(default=False)

    def local_authorities_covered(self):
        return CourtLocalAuthorityAreaOfLaw.objects.filter(
            court=self.court,
            area_of_law=self.area_of_law
        )

    def __str__(self):
        return "%s deals with %s (spoe: %s)" % (self.court.name,
                                                self.area_of_law.name,
                                                self.single_point_of_entry)


class AddressType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CourtAddress(models.Model):
    address_type = models.ForeignKey(AddressType, models.CASCADE)
    court = models.ForeignKey(Court, models.CASCADE)
    address = models.TextField()
    address_cy = models.TextField(null=True, blank=True, default=None)
    postcode = models.CharField(max_length=255)
    town_name = models.CharField(null=True, max_length=255, default=None)
    town_name_cy = models.CharField(null=True, max_length=255, default=None)

    def __str__(self):
        return "%s for %s is %s, %s, %s" % (self.address_type.name, self.court.name, self.address, self.postcode, self.town_name)

    def line(self):
        lines = self.address.splitlines()
        return "%s, %s, %s" % (', '.join(lines), self.town_name, self.postcode)


class Contact(models.Model):
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    sort_order = models.IntegerField(null=True, default=None)
    explanation = models.CharField(null=True, max_length=85)
    in_leaflet = models.BooleanField(default=False)
    explanation_cy = models.CharField(null=True, max_length=85)

    def __str__(self):
        return "%s, %s: %s" % (self.name, self.explanation, self.number)

    @property
    def order_label(self):
        return "%s" % self.name


class CourtContact(models.Model):
    contact = models.ForeignKey(Contact, models.CASCADE)
    court = models.ForeignKey(Court, models.CASCADE)

    def __str__(self):
        return "%s for %s is %s" % (self.contact.name, self.court.name, self.contact.number)


class Email(models.Model):
    description = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    explanation = models.CharField(null=True, max_length=85)
    explanation_cy = models.CharField(null=True, max_length=85)

    def __str__(self):
        return "%s: %s" % (self.description, self.address)

    @property
    def order_label(self):
        return "%s" % self.description


class CourtEmail(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    email = models.ForeignKey(Email, models.CASCADE)
    order = models.IntegerField(null=False, default=0)

    def __str__(self):
        return "%s has email: %s" % (self.court.name, self.email.description)


class CourtType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class CourtCourtType(models.Model):
    court = models.ForeignKey(Court, models.CASCADE)
    court_type = models.ForeignKey(CourtType, models.CASCADE)

    def __str__(self):
        return "Court type for %s is %s" % (self.court.name, self.court_type.name)


class DataStatus(models.Model):
    data_hash = models.CharField(max_length=255)
    last_ingestion_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Current data hash: %s, last update: %s" % (self.data_hash, self.last_ingestion_date)


class ParkingInfo(models.Model):
    onsite = models.CharField(max_length=1024, null=True, default=None)
    offsite = models.CharField(max_length=1024, null=True, default=None)
    blue_badge = models.CharField(max_length=1024, null=True, default=None)

    def __str__(self):
        return "Parking onsite: %s, Parking offsite: %s, Parking blue-badge: %s" % (self.onsite,
                                                                                    self.offsite,
                                                                                    self.blue_badge)


class EmergencyMessage(models.Model):
    message = models.TextField(blank=True)
    message_cy = models.TextField(blank=True, null=True, default=None)
    show = models.BooleanField(default=False)

    def __str__(self):
        return self.message

