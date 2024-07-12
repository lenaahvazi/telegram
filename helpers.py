import requests

import config


def update_config_file(updates):
    lines = []
    with open(config.CONFIG_FILE_PATH, 'r') as file:
        lines = file.readlines()

    with open(config.CONFIG_FILE_PATH, 'w') as file:
        for line in lines:
            for key, value in updates.items():
                if line.startswith(f"{key} ="):
                    if isinstance(value, str):
                        file.write(f"{key} = '{value}'\n")
                    else:
                        file.write(f"{key} = {value}\n")
                    break
            else:
                file.write(line)


def register():
    try:
        url = config.productCatalogURL + config.registrationEndpoint
        params = {
            "deviceName": config.serviceName,
        }

        response = requests.get(url, params=params)
        response_data = response.json()

        updates = {
            'historicalDataIP': response_data.get('historicalDataIP', config.historicalDataIP),
            'ip': response_data.get('ip', config.ip),
            'productCatalogURL': response_data.get('productCatalogURL', config.productCatalogURL),
            'registrationEndpoint': response_data.get('registrationEndpoint', config.registrationEndpoint),
            'messageBrokerIP': response_data.get('messageBrokerIP', config.messageBrokerIP),
            'messageBrokerPort': response_data.get('messageBrokerPort', config.messageBrokerPort),
            'registerInterval': response_data.get('registerInterval', config.registerInterval),
            'status': response_data.get('status', config.status),
            'uacIP': response_data.get('uacIP', config.uacIP),
            'warningTopic': response_data.get('warningTopic', config.warningTopic),
            'getPlaceAdminAPI': response_data.get('getPlaceAdminAPI', config.getPlaceAdminAPI),
            'getPlacesByUsernameAPI': response_data.get('getPlacesByUsernameAPI', config.getPlacesByUsernameAPI),
            'getReportAPI': response_data.get('getReportAPI', config.getReportAPI),
            'getSensorMeasurementAPI': response_data.get('getSensorMeasurementAPI', config.getSensorMeasurementAPI),
            'manageSensorsAPI': response_data.get('manageSensorsAPI', config.manageSensorsAPI),
            'manageSingleSensorAPI': response_data.get('manageSingleSensorAPI', config.manageSingleSensorAPI),
            'token': response_data.get('token', config.token)
        }

        update_config_file(updates)

        return "The new configurations saved successfully.", 200

    except Exception as e:
        return f"An error occurred: {e}", 500
