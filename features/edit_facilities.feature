Feature: Edit facilities for a given court

  Background:
    Given "admin" as the persona
    And I log in to the admin interface
    And I visit "/staff/court/1/facility"

  Scenario: Update existing facility
    When I select "Security arch" from "id_form-6-name"
    And I fill in rich editor "form-6-description" with "Test fac description"
    And I press "Update"
    And I view court in the new window
    Then I should see "Test fac description"

  Scenario: Add new facility
    When I visit "/staff/court/1/add_facility"
    And I select "Disabled toilet" from "id_name"
    And I fill in rich editor "description" with "Test new fac description"
    And I press "Save"
    And I view court in the new window
    Then I should see "Test new fac description"
    And I should see an image with text "Disabled toilet"

  Scenario: Delete existing facility
    When I remove the first form instance
    And I press "Update"
    And I view court in the new window
    Then I should not see "Guide dogs and helping dogs welcome"

  Scenario: Attempt duplicate facility
    When I select "Security arch" from "id_form-0-name"
    And I press "Update"
    Then I should see "Court already has this facility type listed"

  Scenario: No description validation for existing facility
    When I clear rich editor "form-0-description"
    And I press "Update"
    Then I should see "You are missing a required field"

  Scenario: No description validation for new facility
    When I visit "/staff/court/1/add_facility"
    And I select "Public toilets" from "id_name"
    And I press "Save"
    Then I should see "You are missing a required field"