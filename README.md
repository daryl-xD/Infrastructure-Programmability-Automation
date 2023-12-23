# Build and Test
 
```ansible-playbook playbook_name.yml -i inventory```

# DESCRIPTION :


### HOSTNAME 

This playbook uses the hostname module to set the hostname on all hosts, and then uses the lineinfile module to update the hostname in the /etc/hosts and /etc/hostname files. The when clause is used to ensure that the hostname is only updated in these files if the hostname was changed by the hostname module.



### NFTables
This playbook first flushes any existing rules in the input chain of the filter table, and then sets the default policy to drop. It then allows minimal traffic for services to work by allowing established and related connections.

Next, the playbook allows SSH and ICMP traffic from the IP addresses or hostnames specified in the trusted list by adding rules to the input chain of the filter table.

Finally, the playbook saves the rules to a file, enables the nftables service, and makes sure that the nftables service is started and enabled on boot. It also restarts the nftables service to apply the changes.

### DNS SLAVE/MASTER PART 
This template is similar to the one for the DNS master, but it defines the DNS zones as slaves and specifies the IP address of the master DNS server using the masters directive.
As with the master template, you will need to customize this template to match your specific DNS configuration requirements. You can use the {{ domain }} and {{ master_ip }} variables to insert the values defined in the playbook.
To use this template in the playbook, you will need to specify the src and dest parameters in the template module, just as with the master template.

### DNS CLIENT 

This playbook configures the primary and secondary DNS servers, as well as the DNS suffix, on all hosts in the inventory. It uses the lineinfile module to insert or update the relevant lines in the /etc/resolv.conf file.
The primary_dns variable is set to the IP address of the first host in the dns group, and the secondary_dns variable is set to a comma-separated list of the IP addresses of the remaining hosts in the group. These variables are used to configure the primary and secondary DNS servers, respectively. The dns_suffix variable is used to set the DNS suffix for all hosts.
To use this playbook, you will need to have the dns group defined in your /etc/ansible/hosts file, as well as the IP addresses or hostnames of the other hosts in the inventory.

This will configure the DNS client settings on all hosts in the inventory. Note that the playbook includes a handler to restart the network service after the changes are made, so you may experience a brief interruption in network connectivity.

### HA INTRANET 

This playbook installs Keepalived and HAProxy on all hosts in the ha group and then uses templates to generate the configuration files for both services. The keepalived.conf.j2 template configures Keepalived to use the last host in the ha group as the VRRP master and assigns the floating_ip to the master. The haproxy.cfg.j2 template configures HAProxy to load balance HTTP requests to all available web servers using round-robin scheduling and to add the x-haproxy-host header with the hostname of the current HAProxy host.

To use this playbook, you will need to create the keepalived.conf.j2 and haproxy.cfg.j2 templates and place them in the same directory as the playbook. You will also need to have the ha group defined in your /etc/ansible/hosts file, as well as the IP addresses or hostnames of the web servers that you want to load balance.

This will install and configure Keepalived and HAProxy on all hosts in the ha group. Make sure to replace the IP address and password in the floating_ip and vrrp_password variables with the correct values for your environment.

### NFS SHARE 

The playbook uses the lvol module to create logical volumes for each NFS share specified in the shares variable. It then formats the logical volumes using the filesystem module, and mounts the NFS shares using the mount module.

Finally, the playbook uses the template module to create an /etc/exports file with the appropriate entries for each NFS share, using the HOST variable to specify the host that is allowed to access the share.

Note that this playbook assumes that there is a volume group called "nfs" already created on the host. It also uses the ext4 filesystem to format the logical volumes, but you can choose any filesystem that is supported by the host.

exports.j2
This template loops through the shares variable and generates an entry for each NFS share, using the share.name and host variables to specify the path and host that is allowed to access the share. The rw,sync,no_subtree_check options specify that the share is writable, changes are immediately flushed to disk, and subtree checking is disabled.

To use this template with the playbook example provided above, you can save the template as exports.j2 and place it in the same directory as the playbook.

### WEB
This playbook installs the Apache web service using the package module, and then uses the template module to configure the local website and virtual host.

The index.html.j2 template file is used to generate the content for the local website, using the hostname and webcolor variables to display the message and set the text color. The virtualhost.conf.j2 template file is used to generate the virtual host configuration, using the hostname variable to display the hostname of the web server that served the site.

Finally, the playbook uses the service module to restart the Apache web service to apply the changes.

Note that this playbook assumes that the index.html.j2 and virtualhost.conf.j2 template files exist and are in the correct format. You can customize the templates to display the desired content and configure the virtual host as needed.

virtualhost.conf.j2 
This template defines a virtual host listening on port 8081, with the server name intranet.applix.com and the document root /var/www/html/intranet. It also includes directives to configure the error and access logs, and to allow access to the /var/www/html/intranet directory.

To use this template with the playbook example provided above, you can save the template as virtualhost.conf.j2 and place it in the same directory as the playbook. You can then use the template module to generate the virtual host configuration file, using the hostname variable to display the hostname of the web server that served the site.
### USERS

This playbook uses the import_user module to import users from the /etc/ansible/users.csv file on all LIN hosts. The loop directive is used to iterate over the rows in the CSV file, and the when clause ensures that the task is only run on Linux hosts.

The update_password option is set to always, which means that the password will be updated if there is already an existing user with the same username and UID. If you want to ensure that the password is not changed if there is already an existing user, you can set the update_password option to on_create, which will only update the password when creating a new user.

Note that this playbook assumes that the /etc/ansible/users.csv file exists and is in the correct format. The file should contain rows with the following format: name,password,uid.

### BACKUP 

This playbook installs the rsync package using the package module, and then uses the template module to create a backup script, a systemd service, and a systemd timer.

The backup_dns.sh.j2 template file is used to generate the backup script, which uses rsync to copy the DNS zone files from the local host to the backup destination. The backup_dns.service.j2 and backup_dns.timer.j2 template files are used to generate the systemd service and timer, which are used to run the backup script on a regular basis.

Finally, the playbook uses the systemd module to enable and start the timer, ensuring that the backup job runs every 5 minutes.

Note that this playbook assumes that the backup_dns.sh.j2, backup_dns.service.j2, and backup_dns.timer.j2 template files exist and are in the correct format. You can customize the templates to configure the backup script, service, and timer as needed.

backup_dns.sh.j
This script uses rsync to copy the named.conf.local file, which contains the DNS zone definitions, to the backup destination, with the file format YYYY-MM-DD_hh-mm-ss_[hostname].tar.gz. The --delete option ensures that deleted files are removed from the backup destination.

backup_dns.timer.j2
This template defines a timer that runs the backup_dns.service unit every 5 minutes, as specified by the OnUnitActiveSec option. The WantedBy option specifies that the timer should be activated when the timers.target unit is reached.

To use this template with the playbook provided above, you can save the template as backup_dns.timer.j2 and place it in the same directory as the playbook. You can then use the template module to generate the systemd timer file, and the systemd module to enable and start the timer.
