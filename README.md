# springrts matrix synapse uberserver xmlrpc password provider


## Configure
Add or amend the `password_providers` entry like so:
```
password_providers:
  - module: "spring_auth_provider.SpringRTSAuthProvider"
    config:
      enabled: true:w
      endpoint: "http://localhost:8300/"
      domain: "springrts.com"
```