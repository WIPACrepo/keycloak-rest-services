/**
 * WLCG / SciTokens scope mapper.
 * 
 * Takes storage scopes and verifies them via an external microservice.
 * 
 * Requires two ENV variables:
 * * WLCG_AUTH_URL: the address of the validating microservice
 * * WLCG_AUTH_SECRET: a shared secret with the microservice for auth
 * 
 * 
 * Available variables from Keycloak:
 * user - the current user
 * realm - the current realm
 * token - the current token
 * userSession - the current userSession
 * keycloakSession - the current keycloakSession
 */
var Context = new JavaImporter(java.net, java.io, java.lang, org.keycloak.jose.jwk);

var scopes = '';
try {
    scopes = token.getScope();
} catch (e) {
    scopes = '';
}
print('Scopes desired: ', scopes);

// split out scopes we handle, so they don't get approved without a valid response
var new_scopes = [];
var storage_scopes = [];
if (scopes !== null && scopes != '') {
    var scopes_list = scopes.split(" ");
    scopes_list.forEach(function(s){
        if (s.startsWith('storage.')) {
            storage_scopes.push(s);
        } else {
            new_scopes.push(s);
        }
    });
}

// talk to WLCG token service for approval
with (Context) {
    var url = System.getenv('WLCG_AUTH_URL');
    if (url) {
        var secret = System.getenv('WLCG_AUTH_SECRET');
        var url = new URL(url);
        var connection = url.openConnection();
        connection.setDoOutput(true);
        connection.setDoInput(true);
        connection.setRequestMethod('POST');
        connection.setConnectTimeout(3000); // 3s
        connection.setReadTimeout(6000); // 6s
        connection.setRequestProperty('Content-Type', 'application/json; charset=UTF-8');
        connection.setRequestProperty('Accept', 'application/json');
        if (secret) {
            connection.setRequestProperty('Authorization', 'bearer '+secret);
        }
        // set body
        var data = {
            'username': user.getUsername(),
            'scopes': storage_scopes.join(' ')
        };
        try {
            var output = connection.getOutputStream();
            output.write(JSON.stringify(data).getBytes("UTF-8"));
            output.flush();
            output.close();
    
            var respCode = connection.getResponseCode();
            if (respCode == 200) {
                var input = '';
                var br = new BufferedReader(new InputStreamReader(connection.getInputStream()));
                var tmp = null;
                while((tmp = br.readLine()) !== null) {
                    input += tmp;
                }
                br.close();
                var body = JSON.parse(input);
                if ('scopes' in body && body['scopes'] != '') {
                    // add any approved scopes
                    new_scopes = new_scopes.concat(body['scopes'].split(" "));
                }
            } else {
                print('Response code : ' + respCode);
            }
            connection.disconnect();
        } catch (e) {
            print('Failure communicating with WLCG_AUTH_URL', e)
        }
    } else {
        print('env WLCG_AUTH_URL is not defined!')
    }
}

token.setScope(new_scopes.join(" "));
