Home = Vue.component('page-home', {
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
</article>
    `
})

Register = Vue.component('page-register', {
    data: function(){
        return {
            title: ''
        }
    },
    template: `
        <article>
            <h2>Register a new account</h2>
        </article>
    `
})

Login = Vue.component('page-login', {
    data: function(){
        return {
            title: ''
        }
    },
    template: `
        <article class="login">
            <h2>Login to an existing account</h2>
        </article>
    `
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
            console.log('path:'+this.path+'   current:'+this.current)
            return {
                active: this.path == this.current
            }
        },
    },
    methods: {
        gotopage: function() {
            router.push(this.path)
        }
    },
    beforeRouteEnter(to, from, next) {
        this.current = to.params.route
        next()
    },
    template: '<li :class="classObj" @click="gotopage"><router-link :to="path">{{ name }}</router-link></li>'
});

var page_data = {
    pages: [
        { id: 'home', name: 'Home' },
        { id: 'register', name: 'Register' }
    ],
    page_id: 'home'
};


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
  { path: '/register', name: 'register', component: Register },
  { path: '/login', name: 'login', component: Login }
];

var router = new VueRouter({
    mode: 'history',
    routes: routes,
    scrollBehavior: scrollBehavior
})

var app = new Vue({
    el: '#page-container',
    data: {
        routes: routes,
        current: '/'
    },
    router: router,
    computed: {
        visibleRoutes: function() {
            var current = this.current;
            return this.routes.filter(function (r) {
                console.log('filter route '+r.path+'. current='+current)
                if (r.path == '/register' && current != '/register')
                    return false
                return true
            })
        }
    },
    watch: {
        '$route.currentRoute.path': {
            handler: function() {
                console.log('currentPath update:'+router.currentRoute.path)
                this.current = router.currentRoute.path
            },
            deep: true,
            immediate: true,
        }
    }
})
