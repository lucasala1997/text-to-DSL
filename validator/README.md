# Validator - DSL Sensor Validator

This project provides a simple Node.js-based API to validate DSL (Domain-Specific Language) output for sensors. It compares expected and generated DSL outputs by parsing them and checking for equality. The validation process is handled through a POST endpoint.

## Features

- **DSL Parsing**: Utilizes the `@lbdudc/sensor-dsl` package to parse the DSL outputs for sensors.
- **API**: Provides an API endpoint to validate and compare DSL outputs.
- **CORS**: Supports Cross-Origin Resource Sharing, allowing interaction with a client (defined in `.env`).
- **Environment Configuration**: Supports environment variables to configure server behavior.

## Installation

1. Clone the repository.
2. Install the dependencies by running:

   ```bash
   nmv use
   npm install
    ```

3. Start the server by running:

   ```bash
    npm run serve
    ```

By default, the server runs on <http://localhost:3000>.

## API Endpoints

POST `/api/sensor/validate`

Validates and compares the expected and generated DSL outputs.

Request Body:

- expected_dsl_output (string): The expected DSL output.
- generated_dsl_output (string): The generated DSL output.

Response:

- is_valid (boolean): Indicates whether the expected and generated DSL outputs are equal.
- full_output (object): Contains the parsed versions of both the expected and generated DSL outputs.

In case of errors, the response includes the error message and the problematic DSL output file.

Example request

```json
{
    "expected_dsl_output": "CREATE PRODUCT ...",
    "generated_dsl_output": "CREATE PRODUCT ..."
}
    ```

Example response

```json
{
  "is_valid": true,
  "full_output": {
    "expected": { /*parsed expected output */ },
    "generated": { /* parsed generated output*/ }
  }
}
```

## Author

Developed by Victor Lamas. Contact: <victor.lamas@udc.es>
