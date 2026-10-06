Feature: Login to Application

  @always_login
  Scenario: Successful login and setup
    Given I open the login page
    When I enter the tenantCode
    Then I click on the Continue button
    When I enter the username
    When I enter the password
    Then I click on the Sign In button
    Then I should see the dashboard page
    Then I expand all menus in the toolbar