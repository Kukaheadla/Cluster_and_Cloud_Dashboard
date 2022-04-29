. ./openrc.sh

ansible-playbook -i hosts -u ubuntu --key-file=~/.ssh/project-key.pem db.yaml