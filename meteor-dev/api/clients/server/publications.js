import { Meteor } from 'meteor/meteor';
import { ClientsCollection } from '../clients';
import { PlaybooksCollection } from '../playbooks';
import { AnsibleCollection } from '../ansible';

Meteor.publish('Clients', function() {
    return ClientsCollection.find()
})

Meteor.publish('Playbooks', function() {
    return PlaybooksCollection.find()
})

Meteor.publish('Ansible', function() {
    return AnsibleCollection.find()
})