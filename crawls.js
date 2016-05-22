var url,cookie,postdata,auth,post,timeout,system = require("system"),page = require("webpage").create();
if (system.args.length !== 6) {
	//console.log(system.args.length)
	console.log('Usage: crawls.js <url> <cookie> <auth> <post> <timeout>');
    phantom.exit();
} else {
	url = system.args[1];
    console.log(url);
	cookie=system.args[2];
	auth=system.args[3];
	post=system.args[4];
	timeout=system.args[5];
    var ajax_urls = Array();
    var start_time = Date.now();
    var first_response = null;
    page.settings.loadImages = false;
    page.settings.resourceTimeout = timeout? timeout * 1000 : 5*1000;
    headers={}
    headers['Cookies']=cookie;
    headers['authorization']=auth;
    page.customHeaders = headers;
    page.settings.userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'

    page.viewportSize = {
            width: 1024,
            height: 768
    };
    page.onInitialized = function() {
    };

    page.onLoadStarted = function() {
            console.log("page.onLoadStarted");
    };
    page.onLoadFinished = function() {
            console.log("page.onLoadFinished");
    };

    //hook url request
    page.onResourceRequested = function(request) {
    	postdata=request.postData?request.postData:""
    	console.log("hook_url:{\"url\":\""+request.url+"\",\"method\":\""+request.method+"\",\"post\":\""+postdata+"\"}hook_url_end")
    };

    page.onResourceReceived = function(response) {
        if (first_response === null && response.status != 301 && response.status != 302) {
                first_response = response;
        }
    };

    //hook alert
    page.onAlert = function(msg) {
        //console.log('ALERT: ' + msg);
        if (msg=="9527"){
        	console.log("alert 9527 maybe xss vlun");
        }
    };

	page.onConsoleMessage = function (msg) {
	    console.log(msg);
	};

    var method = post? "POST":"GET"

    page.open(url, {
            operation: method,
            data: post,
        },
            function(status) {
                if (status !== 'success') {
                console.log('Unable to access network');
                } else {
                    page.evaluate(function() {
                        var allElements = document.getElementsByTagName('*');
                        for ( var i = 0; i<allElements.length; i++ ) {  	
                        	//on event
                            if ( typeof allElements[i].onclick === 'function' ) {
                            	console.log(allElements[i].onclick);
                                allElements[i].click();
                            }
                            if ( typeof allElements[i].onmouseover === 'function' ) {
                            	console.log(allElements[i].onmouseover);
                            	allElements[i].onmouseover()
                            }
                            if ( typeof allElements[i].ondblclick === 'function' ) {
                            	console.log(allElements[i].ondblclick);
                            	allElements[i].ondblclick()
                            }
                            if ( typeof allElements[i].onmousedown === 'function' ) {
                            	console.log(allElements[i].onmousedown);
                            	allElements[i].onmousedown()
                            }                           
                            if ( typeof allElements[i].onmousemove === 'function' ) {
                            	console.log(allElements[i].onmousemove);
                            	allElements[i].onmousemove()
                            }  
                            if ( typeof allElements[i].onmouseout === 'function' ) {
                            	console.log(allElements[i].onmouseout);
                            	allElements[i].onmouseout()
                            }  
                            if ( typeof allElements[i].onmouseup === 'function' ) {
                            	console.log(allElements[i].onmouseup);
                            	allElements[i].onmouseup()
                            }  

                            if (allElements[i].href) {
                                javascript_code = allElements[i].href.match("javascript:(.+)");
                                if (javascript_code){
                                	console.log(javascript_code[0])
                                    eval(javascript_code[0]);
                                }
                            }
                        }
                    });
                }

        window.setTimeout(
            function() {
                console.log("crawl_content:"+page.content+"content_end")
                phantom.exit()
            },
            1000 /* wait 0.5 seconds (5,000ms) */
        );
        //phantom.exit();
        });
	//phantom.exit();

}