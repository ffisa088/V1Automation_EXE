Feature: User Management

  # ─────────────────────────────────────────────
  # TC-UL-01  Add a new User in User Management page
  # ─────────────────────────────────────────────

  Scenario: Add a new User in User Management page
    Then I click on "User Management" from the menu
    Then I wait for 2 seconds
    Given I am on the "User Management" page
    When I click on the Add button
    When I type "Test47" in the input "userName"
    Then I type "john@gmail.com" in the input "email"
    Then I type "6734566567" in the input "mobile"
    Then I select "LOCAL" from the "loginType" dropdown
    Then I type "Mohamed@" in the input "password"
    Then I wait for 1 seconds
    Then I select "Active" from the "userStatus" dropdown
    Then I select "Company Admin" from the "usertype" dropdown
    Then I click on the Next button
    Then I wait for 3 seconds
    Then I check the checkbox with id "chk_option_company_101"
    Then I click on the "default_company_101" button
    Then I select "Main" from the "warehouse" dropdown
    Then I select "Asset" from the "cashledger" dropdown
    Then I wait for 3 seconds
    Then I check the checkbox with id "chk_option_app_5"
    Then I wait for 3 seconds
    Then I check the checkbox with id "chk_option_group_3"
    Then I wait for 3 seconds
    Then I check the checkbox with id "chk_option_group_1"
    Then I click on the Shadrave button


  # ─────────────────────────────────────────────
  # TC-UL-02  Search filters the grid
  # ─────────────────────────────────────────────

  Scenario: Search for a user by name
    Then I type "Test36" in the search bar
    Then I wait for 1 seconds
    Then I clear the search bar


  # ─────────────────────────────────────────────
  # TC-UL-03  View details For Already Created Records
  # ─────────────────────────────────────────────

  Scenario: View details of select user
    Given I am on the "User Management" page
    Then I type "Test47" in the search bar
    Then I wait for 2 seconds
    Then I click "View Details" action for the row where "User" is "Test36" in the table
    Then I wait for 2 seconds
    Then I click on the "closeView" button 
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────
  # TC-UL-04  Edit details For Already Created Records
  # ─────────────────────────────────────────────

  Scenario: Edit details of select user
    Given I am on the "User Management" page
    Then I wait for 2 seconds
    Then I type "Test36" in the search bar
    Then I wait for 2 seconds
    Then I click "Edit User" action for the row where "User" is "Test47" in the table
    Then I wait for 2 seconds
    Then I click on the Next button
    Then I wait for 3 seconds
    Then I check the checkbox with id "chk_option_app_10203165"
    Then I click on the "cancel" button 
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────────
  # TC-UL-05 Search Employee Using User Name Filter
  # ─────────────────────────────────────────────────

  Scenario: Search Employee Using User Name Filter
    Given I am on the "User Management" page
    Then I click on the "openFilters" button
    Then I click on the "userAddFilterRow" button
    Then I click on the "userAddFilterChip_UserName" button
    Then I wait for 2 seconds
    Then I click on the "userFilterCombo_0" button
    Then I wait for 2 seconds
    Then I check the checkbox labelled "demo"
    Then I check the checkbox labelled "test"
    Then I click on the "userApplyFilters" button
    Then I wait for 2 seconds
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────────
  # TC-UL-06 Search Employee Using User type Filter
  # ─────────────────────────────────────────────────

  Scenario: Search Employee Using User type Filter
    Given I am on the "User Management" page
    Then I click on the "openFilters" button
    Then I click on the "userAddFilterRow" button
    Then I click on the "userAddFilterChip_UserType" button
    Then I wait for 2 seconds
    Then I click on the "userFilterCombo_1" button
    Then I check the checkbox labelled "EMPLOYEE"
    Then I click on the "userApplyFilters" button
    Then I wait for 2 seconds
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────────
  # TC-UL-07 Search Employee Using Status Filter
  # ─────────────────────────────────────────────────

  Scenario: Search Employee Using Status Filter
    Given I am on the "User Management" page
    Then I click on the "openFilters" button
    Then I click on the "userAddFilterRow" button
    Then I click on the "userAddFilterChip_Status" button
    Then I wait for 2 seconds
    Then I click on the "userFilterCombo_2" button
    Then I check the checkbox labelled "Active"
    Then I click on the "userApplyFilters" button
    Then I wait for 2 seconds
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────────
  # TC-UL-08 Search Employee Using Theme Filter
  # ─────────────────────────────────────────────────

  Scenario: Search Employee Using Theme Filter
    Given I am on the "User Management" page
    Then I click on the "openFilters" button
    Then I click on the "userAddFilterRow" button
    Then I click on the "userAddFilterChip_ThemeName" button
    Then I click on the "userFilterCombo_3" button
    Then I check the checkbox labelled "blue"
    Then I click on the "userApplyFilters" button
    Then I wait for 2 seconds
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────────
  # TC-UL-09 Search Employee Using Email Filter
  # ─────────────────────────────────────────────────

  Scenario: Search Employee Using Email Filter
    Given I am on the "User Management" page
    Then I click on the "openFilters" button
    Then I click on the "userAddFilterRow" button
    Then I click on the "userAddFilterChip_Email" button
    Then I wait for 2 seconds
    Then I type "@gmail.com" in the input "inp_userFilterValue_4"
    Then I click on the "userApplyFilters" button
    Then I wait for 2 seconds
    Then I click on the "clear_filters" button


  # ─────────────────────────────────────────────────
  # TC-UL-10 Search Employee Using Mobile number Filter
  # ─────────────────────────────────────────────────

  Scenario: Search Employee Using Mobile number Filter
    Given I am on the "User Management" page
    Then I click on the "openFilters" button
    Then I click on the "userAddFilterRow" button
    Then I wait for 2 seconds
    Then I click on the "userAddFilterChip_MobileNo" button
    Then I wait for 2 seconds
    Then I type "123" in the input "inp_userFilterValue_5"
    Then I click on the "userApplyFilters" button
    Then I wait for 2 seconds
    Then I click on the "clear_filters" button



