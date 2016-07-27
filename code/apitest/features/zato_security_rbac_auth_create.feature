@security.rbac-auth
Feature: : zato.security.rbac-auth.create
  # Enter feature description here

  @security.rbac-auth.create
  Scenario: Set up

    Given I store a random string under "url_path"
    Given I store a random string under "basic_password"
    Given I store a random string under "tech_username"
    Given I store a random string under "tech_password"


################### Create RBAC Role ##############################
  @security.rbac-auth.create
  Scenario: Invoke zato.security.rbac.client-role.create

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.rbac.role.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is a random string
    Given JSON Pointer "/parent" in request is "root"


    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And I store "/zato_security_rbac_auth_create_response/id" from response under "role_id"

    And I sleep for "1"


################## Create tech account ############################
  @security.rbac-auth.create
  Scenario: Create a new technichal account

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.tech-account.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is "#tech_username"
    Given JSON Pointer "/is_active" in request is "true"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And I store "/zato_security_tech_account_create_response/name" from response under "tech_name"
    And I store "/zato_security_tech_account_create_response/id" from response under "tech_id"

    And I sleep for "1"

  @security.rbac-auth.create
  Scenario: Set password for our tech account

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.tech-account.change-password"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#tech_id"
    Given JSON Pointer "/password1" in request is "#tech_password"
    Given JSON Pointer "/password2" in request is "#tech_password"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"

    And I sleep for "1"


################### Create RBAC Client Role ##############################
  @security.rbac-auth.create
  Scenario: Invoke zato.security.rbac.client-role.create

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.rbac.client-role.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/client" in request is "#tech_id"
    Given JSON Pointer "/role" in request is "#role_id"


    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And I store "/zato_security_rbac_auth_create_response/id" from response under "client_role_id"

    And I sleep for "1"



################# Create HTTP Channel with rbac security ##############################

  @security.rbac-auth.create
  Scenario: Create an HTTP channel for zato.ping service to be executed with the security definition created

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.http-soap.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is a random string
    Given JSON Pointer "/is_active" in request is "true"
    Given JSON Pointer "/connection" in request is "channel"
    Given JSON Pointer "/transport" in request is "plain_http"
    Given JSON Pointer "/is_internal" in request is "false"
    Given JSON Pointer "/url_path" in request is "/apitest/security/tech-account/ping"
    Given JSON Pointer "/service" in request is "zato.ping"
    Given JSON Pointer "/data_format" in request is "json"
    Given JSON Pointer "/method" in request is "GET"
    Given JSON Pointer "/security_id" in request is "#tech_id"
    Given JSON Pointer "/has_rbac" in request is "true"

    When the URL is invoked

    Then status is "200"
    And I store "/zato_http_soap_create_response/name" from response under "ping_channel_name"
    And I store "/zato_http_soap_create_response/id" from response under "ping_channel_id"

    And I sleep for "1"


  @security.rbac-auth.create
  Scenario: Test the channel with valid credentials

    Given address "$ZATO_API_TEST_SERVER"
    Given header "X_ZATO_USER" "#tech_username"
    Given header "X_ZATO_PASSWORD" "#tech_password"

    Given URL path "/apitest/security/tech-account/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    Then status is "200"

    Then JSON Pointer "/zato_ping_response/pong" is "zato"

    And I sleep for "1"


  @security.rbac-auth.create
  Scenario: Test the channel with invalid credentials

    Given address "$ZATO_API_TEST_SERVER"
    Given header "X_ZATO_USER" "#tech_username"
    Given header "X_ZATO_PASSWORD" "#invalid_password"

    Given URL path "/apitest/security/tech-account/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    Then status is "401"
    And JSON Pointer "/zato_env/result" is "ZATO_ERROR"

    And I sleep for "1"


  @security.rbac-auth.create
  Scenario: Delete created HTTP channel

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.http-soap.delete"
    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#ping_channel_id"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"

    And I sleep for "1"


  @security.rbac-auth.create
  Scenario: Delete the technical account we just used

    Given address "$ZATO_API_TEST_SERVER"
    Given Basic Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.tech-account.delete"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#tech_id"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"

    And I sleep for "1"
