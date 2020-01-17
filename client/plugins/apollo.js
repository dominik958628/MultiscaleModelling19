// https://apollo.vuejs.org/guide/apollo/subscriptions.html#setup

import Vue from 'vue'
import { ApolloClient } from 'apollo-client'
import { HttpLink } from 'apollo-link-http'
import { InMemoryCache } from 'apollo-cache-inmemory'
// New Imports
import { split } from 'apollo-link'
import { WebSocketLink } from 'apollo-link-ws'
import { getMainDefinition } from 'apollo-utilities'

import VueApollo from 'vue-apollo'

// Install the vue plugin like before
Vue.use(VueApollo);


export default ({ app }) => {
  console.log("ApP")

  const GRAPHQL_URL = 'localhost:8000';

  const httpLink = new HttpLink({
    // You should use an absolute URL here
    uri: `http://${GRAPHQL_URL}`,
  });

  // Create the subscription websocket link
  const wsLink = new WebSocketLink({
    uri: `ws://${GRAPHQL_URL}`,
    options: {
      reconnect: true,
    },
  });

  // using the ability to split links, you can send data to each link
  // depending on what kind of operation is being sent
  const link = split(
    // split based on operation type
    ({ query }) => {
      const definition = getMainDefinition(query)
      return definition.kind === 'OperationDefinition' &&
        definition.operation === 'subscription'
    },
    wsLink,
    httpLink
  );

  // Create the apollo client
  const apolloClient = new ApolloClient({
    link,
    cache: new InMemoryCache(),
    connectToDevTools: true,
  });

  const apolloProvider = new VueApollo({
    defaultClient: apolloClient,
  });

  app.apolloProvider = apolloProvider
}

