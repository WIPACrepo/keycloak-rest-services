var institution_list = [
    'UWMadison', 'Aachen', 'DESY'
];
var institution_obj = institution_list.reduce( (obj, value) => {
    obj[value] = value;
    return obj
}, {});

var keycloak = new Keycloak({
    url: 'http://127.0.0.1:8080/auth',
    realm: 'IceCube',
    clientId: 'mgmt'
});

Home = {
    data: function(){
        return {
            title: ''
        }
    },
    template: `
<article class="home">
    <h4>Welcome to the IceCube Neutrino Observatory identity management console.</h4>
    <p>Existing users should <router-link to="/login">Login</router-link></p>
    <p>New users should ask their PI for a registration link.</p>
</article>`
}

Register = {
    data: function(){
        return {
            institution: '',
            firstName: '',
            lastName: '',
            authorListName: '',
            valid: true,
            errMessage: '',
            submitted: false
        }
    },
    props: ['institution'],
    computed: {
        validInstitution: function() {
            return this.institution in institution_obj
        },
        validFirstName: function() {
            console.log('validFirstName:'+this.firstName)
            return this.firstName
        },
        validLastName: function() {
            return this.lastName
        },
        validAuthorListName: function() {
            return this.authorListName
        }
    },
    methods: {
        submit: async function(e) {
            // validate
            this.valid = (this.validInstitution && this.validFirstName
                    && this.validLastName && (!this.authorListName || this.validAuthorListName))

            // now submit
            if (this.valid) {
                this.errMessage = 'Submission processing';
                try {
                    const resp = await axios.post('/api/user_registration', {
                        first_name: this.firstName,
                        last_name: this.lastName,
                        author_name: this.authorListName,
                        institution: this.institution
                    });
                    console.log('Response:')
                    console.log(resp)
                    this.errMessage = 'Submission successful'
                    this.submitted = true
                } catch (error) {
                    console.log('error')
                    console.log(error)
                    let error_message = 'undefined error';
                    if (error.response) {
                        if ('code' in error.response.data) {
                            error_message = 'Code: '+error.response.data['code']+'<br>Message: '+error.response.data['error'];
                        } else {
                            error_message = JSON.stringify(error.response.data)
                        }
                    } else if (error.request) {
                        error_message = 'server did not respond';
                    }
                    this.errMessage = '<span class="red">Error in submission<br>'+error_message+'</span>'
                }
            } else {
                this.errMessage = '<span class="red">Please fix invalid entries</span>'
            }
        }
    },
    template: `
<article class="register">
    <h2>Register a new account</h2>
    <form class="newuser" @submit.prevent="submit">
      <div class="entry">
        <span class="red">* entry is requred</span>
      </div>
      <div class="entry">
        <p>Select your institution: <span class="red">*</span></p>
        <select v-model="institution">
          <option disabled value="">Please select one</option>
          <option v-for="inst in institution_list">{{ inst }}</option>
        </select>
        <span class="red" v-if="!valid && !validInstitution">invalid entry</span>
      </div>
      <textinput name="First Name" inputName="first_name" v-model.trim="firstName"
       required=true :valid="validFirstName" :allValid="valid"></textinput>
      <textinput name="Last Name" inputName="last_name" v-model.trim="lastName"
       required=true :valid="validLastName" :allValid="valid"></textinput>
      <textinput name="Author List Name (usually abbreviated)" inputName="authorname"
       v-model.trim="authorListName" :valid="validAuthorListName" :allValid="valid"></textinput>
      <div v-if="errMessage" class="error_box" v-html="errMessage"></div>
      <div class="entry" v-if="!submitted">
        <input type="submit" value="Submit Registration">
      </div>
    </form>
</article>`
}

Login = {
    data: function(){
        return {
            title: ''
        }
    },
    asyncComputed: {
        userinfo: async function() {
            try {
                var ret = await keycloak.loadUserInfo();
                return ret
            } catch (error) {
                return {"error": JSON.stringify(error)}
            }
        }
    },
    template: `
<article class="login">
    <h2>User details:</h2>
    <div v-for="(value, name) in userinfo">{{ name }}: {{ value }}</div>
</article>`
}

Error404 = {
    data: function(){
        return {
        }
    },
    computed: {
        'pathMatch': function() {
            return this.$route.params[0];
        }
    },
    template: `
<article class="error">
    <h2>Error: page not found</h2>
    <p><span class="code">{{ pathMatch }}</span> does not exist</p>
</article>`
}

Vue.component('textinput', {
    data: function(){
        return {
            required: false,
            valid: true,
            allValid: true
        }
    },
    props: ['name', 'inputName', 'value', 'required', 'valid', 'allValid'],
    template: `
<div class="entry">
  <p>{{ name }}: <span v-if="required" class="red">*</span></p>
  <input :name="inputName" :value="value" @input="$emit('input', $event.target.value)">
  <span class="red" v-if="!allValid && !valid && (required || value)">invalid entry</span>
</div>`
})

Vue.component('navpage', {
    data: function(){
        return {
            path: '',
            name: '',
            current: ''
        }
    },
    props: ['path', 'name', 'current'],
    computed: {
        classObj: function() {
            console.log('name:'+this.name+'   current:'+this.current)
            return {
                active: this.name == this.current
            }
        },
    },
    beforeRouteEnter(to, from, next) {
        this.current = to.params.route
        next()
    },
    template: '<li :class="classObj"><router-link :to="path">{{ name }}</router-link></li>'
});

// scrollBehavior:
// - only available in html5 history mode
// - defaults to no scroll behavior
// - return false to prevent scroll
const scrollBehavior = function (to, from, savedPosition) {
  if (savedPosition) {
    // savedPosition is only available for popstate navigations.
    return savedPosition
  } else {
    const position = {}

    // scroll to anchor by returning the selector
    if (to.hash) {
      position.selector = to.hash

      // specify offset of the element
      if (to.hash === '#anchor2') {
        position.offset = { y: 100 }
      }

      // bypass #1number check
      if (/^#\d/.test(to.hash) || document.querySelector(to.hash)) {
        return position
      }

      // if the returned position is falsy or an empty object,
      // will retain current scroll position.
      return false
    }

    return new Promise(resolve => {
      // check if any matched route config has meta that requires scrolling to top
      if (to.matched.some(m => m.meta.scrollToTop)) {
        // coords will be used if no selector is provided,
        // or if the selector didn't match any element.
        position.x = 0
        position.y = 0
      }

      // wait for the out transition to complete (if necessary)
      this.app.$root.$once('triggerScroll', () => {
        // if the resolved position is falsy or an empty object,
        // will retain current scroll position.
        resolve(position)
      })
    })
  }
}


var routes = [
  { path: '/', name: 'home', component: Home },
  { path: '/register/:institution', name: 'register', component: Register, props: true },
  { path: '/login', name: 'login', component: Login },
  { path: '*', name: '404', component: Error404, props: true }
];

(async function(){ // startup
    var isAuthenticated = false;
    try {
        isAuthenticated = await keycloak.init();
    } catch (error) {
        console.log("error initializing keycloak")
    }

    var router = new VueRouter({
        mode: 'history',
        routes: routes,
        scrollBehavior: scrollBehavior
    })
    router.beforeEach(async function(to, from, next){
      try {
        await keycloak.updateToken(60);
        isAuthenticated = true;
      } catch (error) {
        isAuthenticated = false;
      }
      console.log('baseurl: '+window.location.origin)

      if (to.name !== 'register' && to.name !== 'home' && !isAuthenticated) {
        // do login process
        console.log("keycloak needs login")
        await keycloak.login({redirectUri:window.location.origin+to.path})
        // next({ name: 'Login' })
      }
      else next()
    })

    var app = new Vue({
        el: '#page-container',
        data: {
            routes: routes,
            current: 'home'
        },
        router: router,
        computed: {
            visibleRoutes: function() {
                var current = this.current;
                return this.routes.filter(function (r) {
                    if (r.path[0] == '*') // filter 404 page
                        return false
                    console.log('filter route '+r.path+'. current='+current)
                    if (r.path.startsWith('/register') && current != 'register')
                        return false
                    return true
                })
            }
        },
        watch: {
            '$route.currentRoute.path': {
                handler: function() {
                    console.log('currentPath update:'+router.currentRoute.path)
                    this.current = router.currentRoute.name
                },
                deep: true,
                immediate: true,
            }
        }
    })
})()
