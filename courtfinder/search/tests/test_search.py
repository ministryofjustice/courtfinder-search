import requests
import re
import lxml.html
from django.test import TestCase, Client
from mock import Mock, patch
from search.court_search import CourtSearch, CourtSearchError, CourtSearchClientError, CourtSearchInvalidPostcode
from search.models import *
from django.conf import settings
from datetime import datetime
from django.core import management
from django.core.management.commands import loaddata


class SearchTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super(SearchTestCase, cls).setUpClass()
        test_data_dir = settings.PROJECT_ROOT +  '/data/test_data/'
        management.call_command('loaddata', test_data_dir + 'test_data.yaml', verbosity=0)
        DataStatus.objects.create(data_hash='415d49233b8592cf5195b33f0eddbdc86cebc72f2d575d392e941a53c085281a')

    def setUp(self):
        self.mapit_patcher = patch('search.court_search.Postcode.mapit')
        self.mock_mapit = self.mapit_patcher.start()
        self.mock_mapit.return_value = {
            "shortcuts": {
                "council": 2491
            },
            "areas": {
                "2491": {"name": "Greater London Authority"}
            },
            "wgs84_lat": 51.46898208902647,
            "wgs84_lon": -0.06624795134523233,
        }

    def tearDown(self):
        self.mapit_patcher.stop()

    def test_format_results_with_postal_address(self):
        c = Client()
        response = c.get('/search/results?q=Accrington')
        self.assertContains(response, "Blackburn")

    def test_search_space_in_name(self):
        c = Client()
        response = c.get('/search/results?q=Accrington+Magistrates')
        self.assertContains(response, "Accrington")

    def test_aol_page(self):
        c = Client()
        response = c.get('/search/aol')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/aol.jinja')
        self.assertContains(response, 'About your issue')

    def test_all_areas_of_law_have_descriptions(self):
        c = Client()
        response = c.get('/search/aol')
        h = lxml.html.fromstring(response.content)
        for label in h.cssselect('#aols .form-label'):
            name = label.cssselect('.aol-name')[0].text
            description = label.cssselect('.aol-description')[0].text
            self.assertNotEqual(description, 'None', '{} has no description'.format(name))

    def test_area_of_law_with_no_description_does_not_error(self):
        aol = AreaOfLaw.objects.create(name='Example')
        c = Client()
        response = c.get('/search/aol')
        self.assertEqual(response.status_code, 200)

    def test_spoe_page_with_children_in_contact_search_courts(self):
        c = Client()
        response = c.get('/search/searchbyPostcodeOrCourtList?aol=Children&spoe=continue', follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertTemplateUsed(response, 'courts/list.jinja')

    def test_spoe_page_with_children_start_search_postcode(self):
        c = Client()
        response = c.get('/search/searchbyPostcodeOrCourtList?aol=Children&spoe=start', follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertTemplateUsed(response, 'search/postcode.jinja')

    def test_spoe_page_with_has_spoe_Divorce(self):
        c = Client()
        response = c.get('/search/spoe?aol=Divorce')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/spoe.jinja')
        self.assertContains(response, '<h1>About your Divorce</h1>')

    def test_spoe_page_with_divorce_proceedings(self):
        c = Client()
        response = c.get('/search/spoe?aol=Divorce')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/spoe.jinja')
        self.assertContains(response, 'I want to start proceedings')

    def test_spoe_page_with_divorce_in_contact(self):
        c = Client()
        response = c.get('/search/spoe?aol=Divorce')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/spoe.jinja')
        self.assertContains(response, 'I am already in contact with a court')

    def test_spoe_page_with_divorce_postcode_start(self):
        c = Client()
        response = c.get('/search/postcode?aol=Divorce&spoe=start')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/postcode.jinja')
        self.assertContains(response, 'You will be directed to your Regional Divorce Centre.')

    def test_spoe_page_with_divorce_postcode_continue(self):
        c = Client()
        response = c.get('/search/postcode?aol=Divorce&spoe=continue')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/postcode.jinja')
        self.assertContains(response, 'You will be directed to your Regional Divorce Centre.')

    def test_spoe_page_with_divorce_in_contact_search_courts(self):
        c = Client()
        response = c.get('/search/searchbyPostcodeOrCourtList?aol=Divorce&spoe=continue', follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertTemplateUsed(response, 'courts/list.jinja')

    def test_spoe_page_with_divorce_start_search_postcode(self):
        c = Client()
        response = c.get('/search/searchbyPostcodeOrCourtList?aol=Divorce&spoe=start', follow=True)
        last_url, status_code = response.redirect_chain[-1]
        self.assertEqual(status_code, 302)
        self.assertTemplateUsed(response, 'search/postcode.jinja')


    def test_spoe_page_without_spoe(self):
        c = Client()
        response = c.get('/search/spoe?aol=Crime', follow=True)
        self.assertContains(response, '<h1>Enter postcode</h1>')

    def test_distance_search(self):
        c = Client()
        response = c.get('/search/results?postcode=SE154UH&aol=Crime')
        self.assertEqual(response.status_code, 200)

    def test_local_authority_search(self):
        c = Client()
        response = c.get('/search/results?postcode=SE154UH&aol=Divorce')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Accrington')

    def test_results_no_query(self):
        c = Client()
        response = c.get('/search/results?q=')
        self.assertRedirects(response, '/search/address?error=noquery', 302)

    def test_results_no_postcode(self):
        c = Client()
        response = c.get('/search/results?aol=Crime&postcode=')
        self.assertRedirects(response, '/search/postcode?error=nopostcode&aol=Crime', 302)

    def test_sample_postcode_all_aols(self):
        c = Client()
        response = c.get('/search/results?postcode=SE15+4UH&aol=All')
        self.assertEqual(response.status_code, 200)

    def test_postcode_aol_Housing(self):
        c = Client()
        response = c.get('/search/postcode?aol=Housing possession')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/postcode.jinja')
        self.assertContains(response, '<h1>Housing Possession</h1>')

    def test_sample_postcode_specific_aol(self):
        c = Client()
        response = c.get('/search/results?postcode=SE15+4UH&aol=Divorce')
        self.assertEqual(response.status_code, 200)

    def test_bad_aol(self):
        c = Client()
        response = c.get('/search/results?postcode=SE15+4UH&aol=doesntexist', follow=True)
        self.assertContains(response, 'your browser sent a request', status_code=400)

    def test_inactive_court_is_not_displaying_in_address_search_results(self):
        c = Client()
        response = c.get('/search/results?q=Some+old', follow=True)
        self.assertContains(response, '<span id="number-of-results">1</span>')

    def test_address_search_single_inactive_court_result_redirects_to_closed_court(self):
        c = Client()
        response = c.get('/search/results?q=Some+old+closed+court', follow=True)
        self.assertContains(response, 'alert')

    def test_substring_should_not_match(self):
        c = Client()
        response = c.get('/search/results?q=ample2', follow=True)
        self.assertContains(response, 'validation-error')

    def test_too_much_whitespace_in_address_search(self):
        c = Client()
        response = c.get('/search/results?q=Accrington++++Magistrates', follow=True)
        self.assertNotContains(response, 'validation-error')

    def test_regexp_city_should_match(self):
        c = Client()
        response = c.get('/search/results?q=accrington', follow=True)
        self.assertNotContains(response, 'validation-error')

    def test_scottish_postcodes(self):
        c = Client()
        response = c.get('/search/results?postcode=G24PP&aol=All')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p id="scotland">')
        response = c.get('/search/results?postcode=AB10+7LY&aol=All')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<p id="scotland">')
        response = c.get('/search/results?postcode=BA27AY&aol=All')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<p id="scotland">')

    def test_redirect_directive_action(self):
        self.mock_mapit.side_effect = CourtSearchInvalidPostcode("MapIt doesn't know this postcode")

        with patch('search.rules.Rules.for_view', Mock(return_value={'action':'redirect', 'target':'search:postcode'})):
            c = Client()
            response = c.get('/search/results?postcode=BLARGH')
            self.assertRedirects(response, '/search/postcode?postcode=BLARGH&error=badpostcode', 302)

    def test_internal_error(self):
        c = Client()
        with patch('search.court_search.CourtSearch.get_courts', Mock(side_effect=CourtSearchError('something went wrong'))):
            response = c.get('/search/results.json?q=Accrington')
            self.assertContains(response, "something went wrong", status_code=500)

    def test_search_no_postcode_nor_q(self):
        c = Client()
        response = c.get('/search/results')
        self.assertRedirects(response, '/search/', 302)

    def test_area_of_law_case_insensitive(self):
        self.assertEqual(len(CourtSearch(postcode='SE154UH', area_of_law='divorce')
                             .get_courts()), 1)

    def test_local_authority_search_ordered(self):
        self.assertEqual(CourtSearch(postcode='SE154UH', area_of_law='Divorce')
                         .get_courts()[0].name, "Accrington Magistrates' Court")

    def test_proximity_search(self):
        self.assertNotEqual(CourtSearch(postcode='SE154UH',
                                        area_of_law='Divorce').get_courts(), [])

    def test_court_address_search_error(self):
        with patch('search.court_search.CourtSearch.get_courts',
                   Mock(side_effect=CourtSearchError('something went wrong'))):
            c = Client()
            with self.assertRaises(CourtSearchError):
                response = c.get('/search/results?q=Accrington')

    def test_court_postcode_search_error(self):
        with patch('search.court_search.CourtSearch.get_courts',
                   Mock(side_effect=CourtSearchError('something went wrong'))):
            c = Client()
            with self.assertRaises(CourtSearchError):
                response = c.get('/search/results?postcode=SE15+4PE')

    def test_address_search(self):
        c = Client()
        response = c.get('/search/results?q=Road')
        self.assertEqual(response.status_code, 200)

    def test_partial_word_match(self):
        c = Client()
        response = c.get('/search/results?q=accrington+court')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Accrington Magistrates')

    def test_unordered_word_match(self):
        c = Client()
        response = c.get('/search/results?q=magistrates+court+accrington')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Accrington Magistrates')

    def test_empty_postcode(self):
        c = Client()
        response = c.get('/search/results?postcode=')
        self.assertEqual(response.status_code, 302)

    def test_broken_postcode(self):
        c = Client()
        response = c.get('/search/results?aol=Divorce&spoe=continue&postcode=NW3+%25+au', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NW3  au')

    def test_ni(self):
        c = Client()
        response = c.get('/search/results?postcode=bt2+3rd&aol=Divorce', follow=True)
        self.assertContains(response, "this tool does not return results for Northern Ireland")

    def test_money_claims(self):
        c = Client()
        response = c.get('/search/results?postcode=sw1h9aj&spoe=start&aol=Money+claims')
        self.assertContains(response, "CCMCC")

    def test_money_claims_heading(self):
        c = Client()
        response = c.get('/search/spoe?aol=Money claims')
        self.assertContains(response, '<h1>About your money claim</h1>')

    def test_money_claims_landing_page_option2(self):
        c = Client()
        response = c.get('/search/spoe?aol=Money claims')
        self.assertContains(response, 'already have a claim')

    def test_money_claims_new_claim(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=start')
        self.assertContains(response, '<h1>For a new claim:</h1>')

    def test_money_claims_new_claim_ccmcc(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=start')
        self.assertContains(response, 'courts/county-court-money-claims-centre-ccmcc')

    def test_money_claims_existing(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=continue')
        self.assertContains(response, '<h1>For an existing claim:</h1>')

    def test_money_claims_aol_has_nearest_court_option(self):
        c = Client()
        response = c.get('/search/spoe?aol=Money+claims')
        self.assertContains(response, 'locate nearest county court for hearing')

    def test_money_claims_nearest_court_option(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=nearest')
        self.assertContains(response, '<h1>Enter postcode</h1>')

    def test_money_claims_nearest_court_option_enter_postcode(self):
        c = Client()
        response = c.get('/search/results?aol=Money%20claims&spoe=nearest&postcode=CF373AF')
        self.assertContains(response, 'Some old open court')

    def test_money_claims_nearest_court_option_enter_postcode_prefix_match(self):
        c = Client()
        response = c.get('/search/results?aol=Money%20claims&spoe=nearest&postcode=CF373AF')
        self.assertContains(response, 'No addresses')

    def test_money_claims_nearest_court_option_enter_postcode_only_money_claims(self):
        c = Client()
        response = c.get('/search/results?aol=Money%20claims&spoe=nearest&postcode=CF373AF')
        self.assertNotContains(response, 'Leaflet Magistrates Court')

    def test_money_claims_existing_online(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=continue')
        self.assertContains(response, 'That was previously entered online')
        self.assertContains(response, 'https://www.gov.uk/make-money-claim-online')

    def test_money_claims_existing_paper(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=continue')
        self.assertContains(response, 'That was previously completed on paper')
        self.assertContains(response, '/courts/county-court-money-claims-centre-ccmcc')

    def test_money_claims_existing_court_known(self):
        c = Client()
        response = c.get('/search/postcode?aol=Money claims&spoe=continue')
        self.assertContains(response, 'If you know a local court is dealing with your claim')
        self.assertContains(response, '/courts/')

    def test_ni_immigration(self):
        c = Client()
        response = c.get('/search/results?postcode=bt23rd&aol=Immigration', follow=True)
        self.assertNotContains(response, "this tool does not return results for Northern Ireland")

    def test_court_postcodes(self):
        court = Court.objects.get(name="Accrington Magistrates' Court")
        self.assertEqual(len(court.postcodes_covered()), 1)

    def test_court_local_authority_aol_covered(self):
        court = Court.objects.get(name="Accrington Magistrates' Court")
        aol = AreaOfLaw.objects.get(name="Divorce")
        court_aol = CourtAreaOfLaw.objects.get(court=court, area_of_law=aol)
        self.assertEqual(len(court_aol.local_authorities_covered()), 1)
        self.assertEqual(str(court_aol.local_authorities_covered()[0]),
                         "Accrington Magistrates' Court covers Southwark Borough Council for Divorce")

    def test_models_unicode(self):
        court = Court.objects.get(name="Accrington Magistrates' Court")
        self.assertEqual(str(court), "Accrington Magistrates' Court")
        cat = CourtAttributeType.objects.create(name="cat")
        self.assertEqual(str(cat), "cat")
        ca = CourtAttribute.objects.create(court=court, attribute_type=cat, value="cav")
        self.assertEqual(str(ca), "Accrington Magistrates' Court.cat = cav")
        aol = AreaOfLaw.objects.create(name="Divorce",
                                        external_link="http://www.gov.uk/child-adoption",
                                        external_link_desc="More information on adoption.")
        self.assertEqual(str(aol), "Divorce")
        self.assertEqual(str(aol.external_link), "http://www.gov.uk/child-adoption")
        self.assertEqual(str(aol.external_link_desc), "More information on adoption.")
        aols = CourtAreaOfLaw.objects.create(court=court, area_of_law=aol)
        self.assertEqual(str(aols), "Accrington Magistrates' Court deals with Divorce (spoe: False)")
        address_type = AddressType.objects.create(name="Postal")
        self.assertEqual(str(address_type), "Postal")
        court_address = CourtAddress.objects.create(address_type=address_type,
                                                    court=court,
                                                    address="The court address",
                                                    postcode="CF34RR",
                                                    town_name="Hobbittown")
        self.assertEqual(str(court_address), "Postal for Accrington Magistrates' Court is The court address, CF34RR, Hobbittown")
        contact = Contact.objects.create(name="Enquiries", number="0123456789", explanation="explanation")
        self.assertEqual(str(contact), "Enquiries, explanation: 0123456789")
        court_type = CourtType.objects.create(name="crown court")
        self.assertEqual(str(court_type), "crown court")
        court_contact = CourtContact.objects.create(contact=contact, court=court)
        self.assertEqual(str(court_contact), "Enquiries for Accrington Magistrates' Court is 0123456789")
        court_court_types=CourtCourtType.objects.create(court=court,
                                                        court_type=court_type)
        self.assertEqual(str(court_court_types), "Court type for Accrington Magistrates' Court is crown court")
        court_postcodes=CourtPostcode.objects.create(court=court,
                                                      postcode="BR27AY")
        self.assertEqual(str(court_postcodes), "Accrington Magistrates' Court covers BR27AY")
        local_authority=LocalAuthority.objects.create(name="Southwark Borough Council")
        self.assertEqual(str(local_authority), "Southwark Borough Council")
        court_local_authority_aol=CourtLocalAuthorityAreaOfLaw(court=court,
                                                               area_of_law=aol,
                                                               local_authority=local_authority)
        self.assertEqual(str(court_local_authority_aol), "Accrington Magistrates' Court covers Southwark Borough Council for Divorce")
        facility=Facility.objects.create(name="sofa", description="comfy leather")
        self.assertEqual(str(facility), "sofa: comfy leather")
        court_facility = CourtFacility.objects.create(court=court, facility=facility)
        self.assertEqual(str(court_facility), "%s has facility %s" % (court.name, facility))
        opening_time = OpeningTime.objects.create(type="open 7/7")
        self.assertEqual(str(opening_time), "open 7/7")
        court_opening_time = CourtOpeningTime.objects.create(court=court, opening_time=opening_time)
        self.assertEqual(str(court_opening_time), "%s has facility %s" % (court.name, opening_time))
        email = Email.objects.create(description="enquiries", address="a@b.com")
        self.assertEqual(str(email), "enquiries: a@b.com")
        court_email = CourtEmail.objects.create(court=court, email=email)
        self.assertEqual(str(court_email), "%s has email: %s" % (court.name, email.description))
        now = datetime.now()
        data_status = DataStatus.objects.create(data_hash="wer38hr3hr37hr")
        self.assertEqual(str(data_status), "Current data hash: %s, last update: %s" %
                         (data_status.data_hash, data_status.last_ingestion_date))
        parking_info = ParkingInfo.objects.create(onsite="foo", offsite="bar", blue_badge="baz")
        self.assertEqual(str(parking_info), "Parking onsite: foo, Parking offsite: bar, Parking blue-badge: baz")

    def test_data_status(self):
        c = Client()
        response = c.get('/search/datastatus')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, '415d49233b8592cf5195b33f0eddbdc86cebc72f2d575d392e941a53c085281a')

    def test_employment_venues_link_in_search_results(self):
        c = Client()
        response = c.get('/search/results?postcode=SE15+4PE&aol=Employment')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'https://www.gov.uk/guidance/employment-tribunal-offices-and-venues')

    def test_social_security_venues_link_in_search_results(self):
        c = Client()
        response = c.get('/search/results?aol=Social+security&postcode=SE15+4PE')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'http://sscs.venues.tribunals.gov.uk/venues/venues.htm')

    def test_tax_venues_link_in_search_results(self):
        c = Client()
        response = c.get('/search/results?aol=Tax&postcode=SE15+4PE')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'https://www.gov.uk/tax-tribunal')

    def test_for_no_venue_links(self):
        c = Client()
        response = c.get('/search/results?aol=Bankruptcy&postcode=SE15+4PE')
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, 'https://www.gov.uk/guidance/employment-tribunal-offices-and-venues')
        self.assertNotContains(response, 'http://sscs.venues.tribunals.gov.uk/venues/venues.htm')
        
    def test_gov_uk_links_exist(self):
        #Cannot use Accrington as it has AoLs hidden
        c = Client()
        response = c.get('/search/results?aol=Bankruptcy&postcode=SA79RB')
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'https://www.gov.uk/bankruptcy')
        self.assertContains(response, 'More information on bankruptcy.')

    def test_courts_cases_heard_hide_aols(self):
        c = Client()
        response = c.get('/search/results?q=Accrington+Magistrates')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Cases heard at this venue')

    def test_courts_cases_heard_show_aols(self):
        c = Client()
        response = c.get('/search/results?q=Tameside+Magistrates')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cases heard at this venue')

    def test_emergency_message_show(self):
        c = Client()
        response = c.get('/search/')
        self.assertEqual(response.status_code, 200)

        em = EmergencyMessage.objects.get()
        if em.show:
            self.assertContains(response, 'Special notice')
            self.assertContains(response, em.message)

    def test_emergency_message_no_show(self):
        c = Client()
        response = c.get('/search/')
        self.assertEqual(response.status_code, 200)

        em = EmergencyMessage.objects.get()
        if not em.show:
            self.assertNotContains(response, 'Special notice')
            self.assertNotContains(response, em.message)

    def test_search_court_location_code(self):
        c = Client()
        response = c.get('/search/results?courtcode=1725')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Accrington Magistrates&#39; Court")
        self.assertNotContains(response, "County Court Money Claims Centre (CCMCC)")
        self.assertNotContains(response, "Tameside Magistrates&#39; Court")

    def test_search_county_location_code(self):
        c = Client()
        response = c.get('/search/results?courtcode=244')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "County Court Money Claims Centre (CCMCC)")
        self.assertNotContains(response, "Accrington Magistrates&#39; Court")
        self.assertNotContains(response, "Tameside Magistrates&#39; Court")

    def test_search_magistrate_location_code(self):
        c = Client()
        response = c.get('/search/results?courtcode=1338')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tameside Magistrates&#39; Court")
        self.assertNotContains(response, "Accrington Magistrates&#39; Court")
        self.assertNotContains(response, "County Court Money Claims Centre (CCMCC)")
