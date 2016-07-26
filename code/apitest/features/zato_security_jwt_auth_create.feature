@security.jwt-auth
Feature: zato.security.jwt-auth.create
  Allows one to create an HTTP jwt Auth definition. Its default password will be a randomly generated UUID4, use zato.security.jwt-auth.change-password to change it.

  @security.jwt-auth.create
  Scenario: Set up

    Given I store a random string under "url_path"
    Given I store a random string under "jwt_username"
    Given I store a random string under "jwt_password"
    Given I store a random string under "invalid_token"


################### Create JWT Auth definition ##############################
  @security.jwt-auth.create
  Scenario: Invoke zato.security.jwt-auth.create

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.jwt-auth.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is a random string
    Given JSON Pointer "/is_active" in request is "true"
    Given JSON Pointer "/username" in request is "#jwt_username"
    Given JSON Pointer "/realm" in request is a random string

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And I store "/zato_security_jwt_auth_create_response/name" from response under "jwt_name"
    And I store "/zato_security_jwt_auth_create_response/id" from response under "jwt_id"

    And I sleep for "1"

  @security.jwt-auth.create
  Scenario: Invoke zato.security.jwt-auth.change-password

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.jwt-auth.change-password"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#jwt_id"
    Given JSON Pointer "/password1" in request is "#jwt_password"
    Given JSON Pointer "/password2" in request is "#jwt_password"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"

############# Create channel and assign previously created JWT Definition ########
  @security.jwt-auth.create
  Scenario: Create HTTP channel for zato.ping service to be executed with the security definition created

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.http-soap.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is a random string
    Given JSON Pointer "/is_active" in request is "true"
    Given JSON Pointer "/connection" in request is "channel"
    Given JSON Pointer "/transport" in request is "plain_http"
    Given JSON Pointer "/is_internal" in request is "false"
    Given JSON Pointer "/url_path" in request is "/apitest/security/jwt-auth/ping"
    Given JSON Pointer "/service" in request is "zato.ping"
    Given JSON Pointer "/data_format" in request is "json"
    Given JSON Pointer "/method" in request is "GET"
    Given JSON Pointer "/security_id" in request is "#jwt_id"

    When the URL is invoked

    Then status is "200"
    And I store "/zato_http_soap_create_response/name" from response under "ping_channel_name"
    And I store "/zato_http_soap_create_response/id" from response under "ping_channel_id"

    And I sleep for "1"

############ Login and get Token (for now assuming that login payload is JSON) #########

  @security.jwt-auth.create
  Scenario: Invoke login endpoint to get an usuable token

    Given address "$ZATO_API_TEST_SERVER"
    Given URL path "/jwt/login"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/username" in request is "#jwt_username"
    Given JSON Pointer "/password" in request is "#jwt_password"

    When the URL is invoked

    Then status is "200"

    And I store header "Authorization" from response under "jwt_token"

########### Invoke service with received token #############################
  @security.jwt-auth.create
  Scenario: Invoke ping service with valid token

    Given address "$ZATO_API_TEST_SERVER"
    Given header "Authorization" "#jwt_token"

    Given URL path "/apitest/security/jwt-auth/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    Then status is "200"

    Then JSON Pointer "/zato_ping_response/pong" is "zato"

  ########### Invoke service with invalid token #############################
  @security.jwt-auth.create
  Scenario: Invoke ping service with invalid token

    Given address "$ZATO_API_TEST_SERVER"
    Given header "Authorization" "#invalid_token"

    Given URL path "/apitest/security/jwt-auth/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    ##### TODO: Add aditional steps once we have more info####
    Then status is "403"

  ########### Expire valid token #############################
  @security.jwt-auth.create
  Scenario: Invoke login endpoint to get an usuable token

    Given address "$ZATO_API_TEST_SERVER"
    Given URL path "/jwt/login"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/username" in request is "#jwt_username"
    Given JSON Pointer "/password" in request is "#jwt_password"
    Given JSON Pointer "/void" in request is "true"

    When the URL is invoked

    ##### TODO: Add aditional steps once we have more info####
    Then status is "200"


########### Invoke service again with valid token to test that it was actually expired #############################
  @security.jwt-auth.create
  Scenario: Invoke ping service with valid token

    Given address "$ZATO_API_TEST_SERVER"
    Given header "Authorization" "#jwt_token"

    Given URL path "/apitest/security/jwt-auth/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    Then status is "403"

######### Delete HTTP Channel ############################################
  @security.jwt-auth.create
  Scenario: Delete created HTTP channel for zato.ping

      Given address "$ZATO_API_TEST_SERVER"
      Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

      Given URL path "/zato/json/zato.http-soap.delete"
      Given format "JSON"
      Given request is "{}"
      Given JSON Pointer "/id" in request is "#ping_channel_id"

      When the URL is invoked

      Then status is "200"
      And JSON Pointer "/zato_env/result" is "ZATO_OK"

  @security.jwt-auth.create
  Scenario: Delete created zato.security.jwt-auth and http channel

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.jwt-auth.delete"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#jwt_id"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"


  ################### Create JWT Auth definition with TTL of 15 secs ##############################
  @security.jwt-auth.create
  Scenario: Invoke zato.security.jwt-auth.create

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.jwt-auth.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is a random string
    Given JSON Pointer "/is_active" in request is "true"
    Given JSON Pointer "/username" in request is "#jwt_username"
    Given JSON Pointer "/realm" in request is a random string
    Given JSON Pointer "/ttl" in request is "15"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"
    And I store "/zato_security_jwt_auth_create_response/name" from response under "jwt_name"
    And I store "/zato_security_jwt_auth_create_response/id" from response under "jwt_id"

    And I sleep for "1"

  @security.jwt-auth.create
  Scenario: Invoke zato.security.jwt-auth.change-password

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.jwt-auth.change-password"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#jwt_id"
    Given JSON Pointer "/password1" in request is "#jwt_password"
    Given JSON Pointer "/password2" in request is "#jwt_password"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"

############# Create channel and assign previously created JWT Definition ########
  @security.jwt-auth.create
  Scenario: Create HTTP channel for zato.ping service to be executed with the security definition created

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.http-soap.create"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/cluster_id" in request is "$ZATO_API_TEST_CLUSTER_ID"
    Given JSON Pointer "/name" in request is a random string
    Given JSON Pointer "/is_active" in request is "true"
    Given JSON Pointer "/connection" in request is "channel"
    Given JSON Pointer "/transport" in request is "plain_http"
    Given JSON Pointer "/is_internal" in request is "false"
    Given JSON Pointer "/url_path" in request is "/apitest/security/jwt-auth/ping"
    Given JSON Pointer "/service" in request is "zato.ping"
    Given JSON Pointer "/data_format" in request is "json"
    Given JSON Pointer "/method" in request is "GET"
    Given JSON Pointer "/security_id" in request is "#jwt_id"

    When the URL is invoked

    Then status is "200"
    And I store "/zato_http_soap_create_response/name" from response under "ping_channel_name"
    And I store "/zato_http_soap_create_response/id" from response under "ping_channel_id"

    And I sleep for "1"

############ Login and get Token (for now assuming that login payload is JSON) #########

  @security.jwt-auth.create
  Scenario: Invoke login endpoint to get an usuable token

    Given address "$ZATO_API_TEST_SERVER"
    Given URL path "/jwt/login"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/username" in request is "#jwt_username"
    Given JSON Pointer "/password" in request is "#jwt_password"

    When the URL is invoked

    Then status is "200"

    And I store header "Authorization" from response under "jwt_token"

########### Invoke service with received token and wait 20 secs #############################
  @security.jwt-auth.create
  Scenario: Invoke ping service with valid token

    Given address "$ZATO_API_TEST_SERVER"
    Given header "Authorization" "#jwt_token"

    Given URL path "/apitest/security/jwt-auth/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    Then status is "200"

    Then JSON Pointer "/zato_ping_response/pong" is "zato"
    And I sleep for "20"

########### Invoke service again to test that token is expired #############################
  @security.jwt-auth.create
  Scenario: Invoke ping service with valid token

    Given address "$ZATO_API_TEST_SERVER"
    Given header "Authorization" "#jwt_token"

    Given URL path "/apitest/security/jwt-auth/ping"

    Given format "JSON"
    Given request is "{}"

    When the URL is invoked

    Then status is "403"


######### Delete HTTP Channel ############################################
  @security.jwt-auth.create
  Scenario: Delete created HTTP channel for zato.ping

      Given address "$ZATO_API_TEST_SERVER"
      Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

      Given URL path "/zato/json/zato.http-soap.delete"
      Given format "JSON"
      Given request is "{}"
      Given JSON Pointer "/id" in request is "#ping_channel_id"

      When the URL is invoked

      Then status is "200"
      And JSON Pointer "/zato_env/result" is "ZATO_OK"

  @security.jwt-auth.create
  Scenario: Delete created zato.security.jwt-auth and http channel

    Given address "$ZATO_API_TEST_SERVER"
    Given jwt Auth "$ZATO_API_TEST_PUBAPI_USER" "$ZATO_API_TEST_PUBAPI_PASSWORD"

    Given URL path "/zato/json/zato.security.jwt-auth.delete"

    Given format "JSON"
    Given request is "{}"
    Given JSON Pointer "/id" in request is "#jwt_id"

    When the URL is invoked

    Then status is "200"
    And JSON Pointer "/zato_env/result" is "ZATO_OK"