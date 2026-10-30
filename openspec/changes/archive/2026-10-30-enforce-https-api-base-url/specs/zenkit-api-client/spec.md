# Spec Delta

## ADDED Requirements

### Requirement: Credentials are sent only over HTTPS

The system SHALL accept only `https` base URLs, so the `Zenkit-API-Key` header is never transmitted
over a plaintext connection. A base URL with any other scheme SHALL be rejected with an actionable
configuration error that names `ZENKIT_API_BASE_URL`.

#### Scenario: Plaintext base URL is rejected

- **WHEN** `ZENKIT_API_BASE_URL` is set to an `http://` URL
- **THEN** configuration loading fails with an error naming `ZENKIT_API_BASE_URL` and stating that
  an HTTPS URL is required

#### Scenario: Plaintext loopback base URL is rejected

- **WHEN** `ZENKIT_API_BASE_URL` is set to `http://127.0.0.1:8080/api/v1` or
  `http://localhost:8080/api/v1`
- **THEN** configuration loading fails with the same HTTPS-required error, because no cleartext
  exception is granted for loopback hosts

#### Scenario: HTTPS base URL is accepted

- **WHEN** `ZENKIT_API_BASE_URL` is set to `https://example.test/api/v1`
- **THEN** configuration loading succeeds and requests resolve against that URL

#### Scenario: Default needs no configuration

- **WHEN** `ZENKIT_API_BASE_URL` is unset or blank
- **THEN** configuration loading succeeds using the HTTPS default `https://zenkit.com/api/v1`
