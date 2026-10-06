Feature: User Managemen

Scenario: Open User Managemen page
	Then I click on "User Management" from the menu
	Then I wait for 3 seconds


  # ─────────────────────────────────────────────
  # TC-UL-01  Add a new User in User Management page
  # ─────────────────────────────────────────────



Scenario: Fill User information page
  Given I am on the "User Management" page
  When I click on the Add button
  When I type "Test6" in the input "userName"
  Then I type "john@gmail.com" in the input "emailas"
  Then I type "6734566567" in the input "mobiles"
  Then I select "LOCAL" from the "loginType" dropdown
  Then I type "Mohamed@" in the input "password"
  Then I wait for 1 seconds
  Then I select "Active" from the "userStatus" dropdown
  Then I select "Admin" from the "usertype" dropdown
  Then I click on the Next button
  


