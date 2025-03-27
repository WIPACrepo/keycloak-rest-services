/**
 * Available variables:
 * user - the current user
 * realm - the current realm
 * token - the current token
 * userSession - the current userSession
 * keycloakSession - the current keycloakSession
 */
var Network = new JavaImporter(java.net, java.io);

var scopes = token.getScope();
print('Existing scopes: '+scopes)
var new_scopes = "";

with (Network) {
    var url = new URL('https://authorlist.icecube.wisc.edu');
    var connection = url.openConnection();
    connection.setRequestMethod('GET');
    connection.connect();
    var respCode = connection.getResponseCode();
    if (respCode == 200) {
        new_scopes = "storage.read:/docs storage.write:/docs"
    } else {
        print('Response code : ' + respCode);
    }
    connection.disconnect();
}

if (scopes) {
    scopes += " "+new_scopes;
} else {
    scopes = new_scopes;
}
token.setScope(scopes);
