from flask import Flask, jsonify, request
import json,socketserver,subprocess,requests

app = Flask(__name__)

@app.route('/customers/', methods=['PUT'])
def update_customers():
    # Print the request data as JSON
    print(request.json)

    # Check if the required fields are present in the request data
    if 'name' not in request.json:
        return jsonify({"error": "name field is required"}), 400

    if 'domain_prefix' not in request.json:
        return jsonify({"error": "domain_prefix field is required"}), 400

    if 'message' not in request.json:
        return jsonify({"error": "message field is required"}), 400

    if 'password' not in request.json:
        return jsonify({"error": "password field is required"}), 400

    if 'username' not in request.json:
        return jsonify({"error": "username field is required"}), 400

    # Extract the fields from the request data
    username = request.json.get('username')
    domain_prefix = request.json.get('domain_prefix')
    name = request.json.get('name')

    # Read the customers data from the JSON file
    with open('/etc/ansible/customers.json', 'r') as file:
        data = json.load(file)
    print(type(data))
    print(len(data))

    # Check if the username, domain prefix, or name are already in use
    if any(d['username'] == username for d in data):
        return jsonify({"error": "username field has to be unique."}), 403

    if any(d['domain_prefix'] == domain_prefix for d in data):
        return jsonify({"error": "domain_prefix field has to be unique."}), 403

    if any(d['name'] == name for d in data):
        return jsonify({"error": "name field has to be unique."}), 403

    # Add the new customer data to the list
    data.append(request.json)
    print(len(data))

    # Write the updated list of customer data to the JSON file
    json_object = json.dumps(data, indent=4)
    with open("/etc/ansible/customers.json", "w") as outfile:
        outfile.write(json_object)

    # Return the updated list of customer data
    return jsonify(data), 200
    

@app.route('/network/devices/stats', methods=['GET'])
def get_interface_stats():
    ip_range = [f"10.22.0.{i}" for i in range(201, 209)]
    management_ip = request.args.get('management_ip')

# If a specific device is specified, make RESTCONF call to that device
    if management_ip:
        # Make RESTCONF call to specific device to retrieve interface data
        headers = {'Accept': 'application/yang-data+json'}
        response = requests.get(f'https://{management_ip}/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces', auth=('appadmin', 'Incheon-2022'), verify=False, headers=headers)
        response2 = requests.get(f'https://{management_ip}/restconf/data/Cisco-IOS-XE-native:native', auth=('appadmin', 'Incheon-2022'), verify=False, headers=headers)

        # If the RESTCONF call fails, return an error message and status code to the client
        if response.status_code != 200:
            return f"Error {response.status_code} occurred while trying to retrieve data from {management_ip}", response.status_code

        # Filter for only active interfaces
        interfaces_list = response.json()['Cisco-IOS-XE-interfaces-oper:interfaces']['interface']
        active_interfaces = [interface for interface in interfaces_list if interface['oper-status'] == 'if-oper-state-ready']
        
        # If no active interfaces were found, return an HTTP not found error to the client
        if not active_interfaces:
            return "No active interfaces found on specified device", 404

        # Make RESTCONF calls to retrieve pkts-in/pkts-out data for each active interface
        device_data = {}
        device_info = {}
        device_info['version'] = response2.json()['Cisco-IOS-XE-native:native']['version']
        device_info['hostname'] = response2.json()['Cisco-IOS-XE-native:native']['hostname']
        device_info['management_ip'] = management_ip
        
        device_info['interfaces'] = []  # Add the 'interfaces' key to the 'device_info' dictionary
        for interface in active_interfaces:
            interface_data = {}
            interface_data['name'] = interface['name']
            interface_data['mac'] = interface['phys-address']
            
            # Make RESTCONF call to retrieve pkts-in data for the interface
            pkts_in_response = requests.get(f'https://{management_ip}/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces/interface={interface_data["name"]}', auth=('appadmin', 'Incheon-2022'), verify=False, headers=headers)
            interface_data['pkts-in'] = pkts_in_response.json()['Cisco-IOS-XE-interfaces-oper:interface']['statistics']['in-unicast-pkts']  
            interface_data['pkts-out'] = pkts_in_response.json()['Cisco-IOS-XE-interfaces-oper:interface']['statistics']['out-unicast-pkts']
            
            device_data['devices'] = [device_info] 
            device_info['interfaces'].append(interface_data)
              
        return jsonify(device_data), 200

    # If no specific device is specified, make RESTCONF calls to all devices and return a list of all active interfaces with pkts-in/pkts-out data
    else:
        all_devices_data = []
        for management_ip in ip_range:
            # Make RESTCONF call to specific device to retrieve interface data
            headers = {'Accept': 'application/yang-data+json'}
            
            try:
               response = requests.get(f'https://{management_ip}/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces', auth=('appadmin', 'Incheon-2022'), verify=False, headers=headers)
               response2 = requests.get(f'https://{management_ip}/restconf/data/Cisco-IOS-XE-native:native', auth=('appadmin', 'Incheon-2022'), verify=False, headers=headers)
            except requests.exceptions.ConnectionError:
               continue
            if response.status_code != 200 or response2.status_code != 200:
               continue

            # Parse the response and get the list of interfaces
            interfaces_list = response.json()['Cisco-IOS-XE-interfaces-oper:interfaces']['interface']

            # Filter the list of interfaces to get a list of active interfaces
            active_interfaces = [interface for interface in interfaces_list if interface['oper-status'] == 'if-oper-state-ready']

            # If no active interfaces were found, continue to the next device in the list
            if not active_interfaces:
                continue

            # Make RESTCONF calls to retrieve pkts-in/pkts-out data for each active interface
            device_data = {}
            device_info = {}
            device_info['version'] = response2.json()['Cisco-IOS-XE-native:native']['version']
            device_info['hostname'] = response2.json()['Cisco-IOS-XE-native:native']['hostname']
            device_info['management_ip'] = management_ip

            device_info['interfaces'] = []  # Add the 'interfaces' key to the 'device_info' dictionary
            for interface in active_interfaces:
                interface_data = {}
                interface_data['name'] = interface['name']
                interface_data['mac'] = interface['phys-address']               

                # Make RESTCONF call to retrieve pkts-in data for the interface
                pkts_in_response = requests.get(f'https://{management_ip}/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces/interface={interface_data["name"]}', auth=('appadmin', 'Incheon-2022'), verify=False, headers=headers)                
                interface_data['pkts-in'] = pkts_in_response.json()['Cisco-IOS-XE-interfaces-oper:interface']['statistics']['in-unicast-pkts']
                interface_data['pkts-out'] = pkts_in_response.json()['Cisco-IOS-XE-interfaces-oper:interface']['statistics']['out-unicast-pkts']

                device_data['devices'] = [device_info] 
                device_info['interfaces'].append(interface_data)

            # Add the data for the current device to the list of all devices data
            all_devices_data.append(device_info)

    # Return the list of all devices data to the client
    return jsonify(all_devices_data), 200
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
