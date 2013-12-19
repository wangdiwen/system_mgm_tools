function isArray(o) {     
    return Object.prototype.toString.call(o) === '[object Array]';      
} 
function isObject(o) {     
    return Object.prototype.toString.call(o) === '[object Object]';      
} 
function isDigit(s)
{
    var patrn = /^(-)*\d*$$/;
    if (patrn.test(s))
        return true;
    return false;
}

function hasChinese(s)
{
    if(/.*[\u4e00-\u9fa5]+.*$/.test(s)) 
        return true;
    if(/.*[\uff01|\uffe5|\u2026|\u2014|\uff08|\uff09]+.*$/.test(s)) 
        return true;
    return false;
}

function sync_ajax(url, type, data, dataType)
{
    if (typeof dataType == "undefined")
        dataType = "json"
    var d = {
        url:url,
        async:false,
        cache:false,
        dataType:dataType,
        data: data,
        type: type
    };
    return $.ajax(d).responseText;
}

function restful_ajax(url, type, data, async, error, success)
{
    var d 
    if (arguments.length == 1)
    {
        d = {
            cache:false
        };
        for (var i in arguments[0])
        {
            d[i] = arguments[0][i]
        }
    }else{
        d = {
            url:url,
            async:async,
            cache:false,
            data: data,
            type: type,
            error: error,
            success: success
        };
    }
    
    return $.ajax(d).responseText;
}

function sleep(numberMillis) {
    var now = new Date();
    var exitTime = now.getTime() + numberMillis;
    while (true) {
        now = new Date();
        if (now.getTime() > exitTime)
            return;
    }
}

function isIp(s)
{
    var patrn = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
    var reg = s.match(patrn);
    if(reg == null)
        return false;
    return true;
}

function isIpWithPort(s)
{
    var patrn = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(:[\d]{1,4})+$/;
    var reg = s.match(patrn);
    if(reg == null)
        return false;
    return true;
}

function isStrictIp(s)
{
    var patrn = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
    var reg = s.match(patrn);
    if(reg == null)
        return false;
    var spec_ip = new Array(["255.255.255.255", "0.0.0.0"]);
    for (var i = 0 ; i < spec_ip.length; i++)
    {
        if (s == spec_ip[i])
            return false;
    }
    var part = s.split(".");
    if (part[0] == 0||
        part[0] > 223)
        return false;
    if (part[3] == "0"
        ||part[3] == "255")
        return false;
    return true;
    
    
    //other method
    var patrn=/^([1-9]|[1-9]\d|1\d{2}|2[0-1]\d|22[0-3])(\.(\d|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])){3}$/; 
    s.match(patrn); 
    if(reg==null) 
        return false; 
    return true; 
}
function isStrictIpWithPort(s)
{
    var patrn = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(:[\d]{1,4})+$/;
    var reg = s.match(patrn);
    if(reg == null)
        return false;
    var spec_ip = new Array(["255.255.255.255", "0.0.0.0"]);
    for (var i = 0 ; i < spec_ip.length; i++)
    {
        if (s == spec_ip[i])
            return false;
    }
    var part = s.split(".");
    if (part[0] == 0||
        part[0] > 223)
        return false;
    if (part[3] == "0"
        ||part[3] == "255")
        return false;
    return true;
}


function isNetWorkIp(s)
{
    var patrn = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
    var reg = s.match(patrn);
    if(reg == null)
        return false;
    var spec_ip = new Array(["255.255.255.255", "0.0.0.0"]);
    for (var i = 0 ; i < spec_ip.length; i++)
    {
        if (s == spec_ip[i])
            return false;
    }
    var part = s.split(".");
    if (part[0] == 0||
        part[0] > 223)
        return false;
    if (part[3] != "0"
        ||part[3] == "255")
        return false;
    return true;
}

function isNetWorkRange(s)
{
    var patrn = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\/([1-9]|1\d|2\d|30)$/;
    var reg = s.match(patrn);
    if(reg == null)
        return false;

    var spec_ip = new Array(["255.255.255.255"]);
    for (var i = 0 ; i < spec_ip.length; i++)
    {
        if (s == spec_ip[i])
            return false;
    }
    var part = s.split(".");
    if (part[0] > 223)
        return false;
    if (part[3] == "255")
        return false;
    return true;
}

function isMask(mask) 
{ 
    var patrn=/^(254|252|248|240|224|192|128|0)\.0\.0\.0|255\.(254|252|248|240|224|192|128|0)\.0\.0|255\.255\.(254|252|248|240|224|192|128|0)\.0|255\.255\.255\.(254|252|248|240|224|192|128|0)$/; 
    var reg = mask.match(patrn); 
    if(reg==null) 
        return false; 
    return true; 
}

function isPort(port)
{
    var patrn=/^([\:]{0,1})([\d]{1,5})?$/; 
    var reg = port.match(patrn); 
    if(reg==null) 
        return false; 
    return true; 
}

function isURL(url) {
    var patrn = /^([0-9a-z\-]+\.)*([0-9a-z][0-9a-z\-]{0,61})?[0-9a-z]\.[a-z]{2,6}$/;
    var reg = url.match(patrn);
    if(reg==null) 
        return false; 
    return true; 
}

function setCookie(name, value) 
{ 
    var argv = setCookie.arguments; 
    var argc = setCookie.arguments.length; 
    var expires = (argc > 2) ? argv[2] : null; 
    if(expires!=null) 
    { 
        var LargeExpDate = new Date (); 
        LargeExpDate.setTime(LargeExpDate.getTime() + (expires*1000*3600*24));         
    } 
    document.cookie = name + "=" + escape (value)+((expires == null) ? "" : ("; expires=" +LargeExpDate.toGMTString())); 
}

function getCookie(Name) 
{ 
    var search = Name + "=" 
    if(document.cookie.length > 0) 
    { 
        offset = document.cookie.indexOf(search) 
        if(offset != -1) 
        { 
            offset += search.length 
            end = document.cookie.indexOf(";", offset) 
            if(end == -1) end = document.cookie.length 
            return unescape(document.cookie.substring(offset, end)) 
        } 
        else return "" 
    } 
} 

function deleteCookie(name) 
{ 
    var expdate = new Date(); 
    expdate.setTime(expdate.getTime() - (86400 * 1000 * 1)); 
    setCookie(name, "", expdate); 
} 

/***********
vmxGrid
***********/

jQuery.vmxGrid = {
    data:[]
};
$.fn.vmxGrid = function(options) {  
    
    var defaults = {
        url: null,
        colModel: [], //{display, name, width, align}
        title: "",
        buttons : [],
        init:false,
        showhead:true,
        showtitle:true
    };    
    var opts = $.extend(defaults, options); 
    var vmxGrid = $(this);
    if (typeof(opts.colModel) == "undefined" || opts.colModel == null)
        opts.colModel = []
    if (opts.colModel.length == 0)
        opts.colModel.push({name: "defaults", display:"&nbsp;", width:"auto", align:"left"});

    // Extend our default options with those provided.    
    opts.mouseover = function(events)
    {
        if (vmxGrid.current_tr == null ||
            vmxGrid.current_tr != events.data.obj)
            vmxGrid.current_tr = events.data.obj
        //$("td:first-child", vmxGrid.current_tr).append(vmxGrid.command_button);
    };
    
    opts.mouseout = function(events)
    {
    };
    
    opts.tr_click = function(events)
    {
        var btn_opts = $(events.data.obj).data("user_option");
        $(vmxGrid.current_tr).data("user_option", opts)
        btn_opts["onpress"](vmxGrid.current_tr);
        return false;
    };
    opts.btn_click = function(events)
    {
        var btn_opts = $(events.data.obj).data("user_option");
        btn_opts["onpress"]();
        return false;
    };
    
    this.each(function() {  

        var tr = null;
        var colModel = opts.colModel;
        var colspan = colModel.length;
        if (typeof(opts.buttons) != "undefined" && opts.buttons.length > 0)
            colspan = colModel.length + 1;
        
        
        var me = $(this);
        $(me).get(0).className = "vmxGrid";
        
        //var opts = $.vmxGrid.opts;
        var container = {};
        
        
        /*
        *   create title
        */
        if (opts.showtitle)
        {
            container.title = document.createElement('div');
            container.title.className = "grid_title";
            container.title.innerHTML = opts.title;
            if (typeof opts.titleappend != "undefined" && opts.titleappend != "")
                $(container.title).append(opts.titleappend)
            $(me).append(container.title);
        }
        
        /*
        *   create table
        */
        container.table = document.createElement('table');
        container.table.className = "grid_table";
        container.table.style.width = "100%";
        
        // create head for table
        if (opts.showhead)
        {
            container.thead = document.createElement('thead');
            tr = document.createElement('tr')
            if (typeof(opts.buttons) != "undefined" && opts.buttons.length > 0)
            {
                var th = document.createElement('th');
                th.style.width = opts.buttons.length * 30 + "px";
                $(tr).append(th);
            }
            for (var i = 0; i < colModel.length; i++)
            {
                var th = document.createElement('th');
                th.innerHTML = colModel[i].display;
                th.name = colModel[i].name;
                if (colModel[i].width != "auto")
                    th.style.width = colModel[i].width + "px";
                th.style.textAlign = colModel[i].align;
                $(tr).append(th);
            }
            $(container.thead).append(tr);
            $(container.table).append(container.thead);
        }
        
        // create body for table
        container.tbody = document.createElement('tbody');
        $(container.table).append(container.tbody);
        
        // create foot for table
        container.tfoot = document.createElement('tfoot');
        tr = document.createElement('tr');

        var td = document.createElement('td');
        //td.setAttribute("colspan", colspan);
        td.colSpan = colspan;
        if  (typeof(opts.foot) != "undefined" && opts.foot.length > 0)
        {
            for (var i = 0 ; i < opts.foot.length; i++)
            {
                if (typeof(opts.foot[i].html) != "undefined")
                {
                    $(td).append(opts.foot[i].html);
                    continue;
                }
                var btn = document.createElement('button');
                btn.className = opts.foot[i]["bclass"];
                btn.innerHTML = opts.foot[i]["name"];
                btn.style.cursor = "hand";
                var btn_opts = {
                    onpress: opts.foot[i]["onpress"]
                };
                $(btn).data("user_option" , btn_opts);
                $(btn).on("click", {obj:$(btn)}, opts.btn_click);
                $(td).append(btn);
            }
        }
        if (typeof(opts.foot)== "undefined" || opts.foot.length == 0)
        {
            td.innerHTML = "&nbsp;";
        }
        $(tr).append(td);
        $(container.tfoot).append(tr);
        $(container.table).append(container.tfoot);
        
        /*
        *  
        */
        
        $(me).append(container.table);
        
        opts.grid = vmxGrid;
        opts.container = container;
        me.data("user_option" , opts);
        
        if (opts.url != null)
        {
            $.vmxGridAdd(me);
        }
        
        
    });
    // Our plugin implementation code goes here.
}; 
jQuery.vmxGridAdd = function(me) {
    var opts = me.data("user_option");
    var container = opts.container;
    //var vmxGrid = opts.grid;
    var colModel = opts.colModel;
    
    var commond_buttons = false;
    if (typeof(opts.buttons) != "undefined" && opts.buttons.length > 0)
        commond_buttons = true;
    var create_tr = function(ret_data)
    {
        tr = document.createElement('tr');
        if (commond_buttons)
        {
            var td = document.createElement('td');
            //$(td).append("<a onclick='alert(123);'>reload</a>");
            td.style.textAlign = "center";
            
            var command_button = document.createElement('div');
            command_button.className = "command";

            for (var i = 0; i < opts.buttons.length; i++)
            {
                    var btn = document.createElement('a');
                    btn.innerHTML = "&nbsp;";
                    btn.setAttribute("href", "javascript:void(0);");
                    btn.setAttribute("title", opts.buttons[i]["name"]);
                    btn.setAttribute("rel", "button_" + opts.buttons[i]["bclass"]);
                    btn.style.width = "20px";
                    btn.style.height = "20px";
                    //btn.setAttribute("type", "button");
                    //btn.setAttribute("alt", opts.buttons[i]["name"]);
                    btn.className = opts.buttons[i]["bclass"];
                    var btn_opts = {
                        onpress: opts.buttons[i]["onpress"]
                    };
                    $(btn).data("user_option" , btn_opts);
                    $(btn).on("click", {obj:$(btn)}, opts.tr_click);
                    //btn.onclick = $.vmxGrid.opts.click;
                    $(command_button).append(btn);
            }
            $(td).append(command_button);
                //$($.vmxGrid.command_button).on("click", function (){alert(123);});
                //$("body").append($.vmxGrid.command_button);
            
            $(tr).append(td);
            //$(td).on("click", function(){alert(1);});
        }
        for (var j = 0; j < colModel.length; j++)
        {
            var td = document.createElement('td');
            var _tmp_data;
            if (isArray(ret_data))
                _tmp_data = ret_data[i];
            else if (isObject(ret_data))
            {
                _tmp_data = ret_data[colModel[j].name];
                if (typeof ret_data[colModel[j].name] == "undefined")
                    _tmp_data = ""
            }
            else
                _tmp_data = ret_data
                
            td.innerHTML = _tmp_data;
            td.style.height = "25px";
            td.style.textAlign = colModel[j].align;
            //$(td).on("click", function(){alert(2);});
            $(tr).append(td);
        }
        $(tr).on("mouseover", {obj:$(tr)}, opts.mouseover);
        $(tr).on("mouseout", {obj:$(tr)}, opts.mouseout);
        $(container.tbody).append(tr);
    };
    var fill_tr = function(tr, ret_data)
    {
        var j = 0;
        var count = colModel.length;
        if (commond_buttons)
        {
            j = 1;
            count++;
        }
        for (; j < count; j++)
        {
            var _tmp_data;
            if (isArray(ret_data))
                _tmp_data = ret_data[i];
            else if (isObject(ret_data))
            {
                _tmp_data = ret_data[colModel[j - 1].name];
                if (typeof ret_data[colModel[j - 1].name] == "undefined")
                    _tmp_data = ""
            }
            else
                _tmp_data = ret_data
                
            if (commond_buttons)
                $("td", tr).get(j).innerHTML = _tmp_data;
            else
                $("td", tr).get(j).innerHTML = _tmp_data;
        }
    };
    var ret = restful_ajax({url:opts.url, type:"GET", async:false, error:function(XMLHttpRequest, textStatus, errorThrown)
    {
        retcode = false
    }, success:function()
    {
        retcode = true;
    }});
    if (retcode)
    {
        var ret_data = $.parseJSON(ret)
        var tr_list;
        if (opts.init)
        {
            var data_size = isArray(ret_data) ? ret_data.length : 1;
            tr_list = $("tr", container.tbody);
            var grid_size = tr_list.size();
            
            if (data_size > grid_size)
            {
                for (var i = 0; i < data_size - grid_size; i++)
                {
                    create_tr({});
                }
            }
            if (data_size < grid_size)
            {
                for (var i = 0; i < grid_size - data_size ; i++)
                {
                    //$("body").append(vmxGrid.command_button);
                    $(tr_list).eq(0).remove();
                    tr_list = $("tr", container.tbody);
                }
            }
            tr_list = $("tr", container.tbody);
        }
        if (isArray(ret_data))
        {
            for (var i = 0; i < ret_data.length; i++)//ret_data.length
            {
                if (opts.init)
                    fill_tr(tr_list.get(i), ret_data[i]);
                else
                    create_tr(ret_data[i]);
            }
        }
        else
        {
            if (opts.init)
                fill_tr(tr_list.get(0), ret_data);
            else
                create_tr(ret_data);
        }
    }
    opts.size = $("tr", container.tbody).size();
    if (!opts.init)
        opts.init = true;
}
$.fn.vmxGridGet = function(index) {
    var ret = null; 
    this.each(function() {  
    //    alert(2);
        //this.className = "vmxGrid";
        var me = $(this)
        var opts = me.data("user_option");
        if (index > opts.size - 1 )
            ret = null;

        ret = opts.container.tbody.children[index]
    });
    return ret;
}
$.fn.vmxGridReload  = function(options) {
    this.each(function() {  
    //    alert(2);
        //this.className = "vmxGrid";
        var me = $(this)
        var opts = me.data("user_option");

        if (opts)
        {
            opts = $.extend(opts, options);
            me.data("user_option", opts)
            $.vmxGridAdd(me);
        }
            
    });
};    
/*****************
vmxTab
*****************/
$.fn.vmxTab = function (options) {
    /*var defaults = {
        url: null,
        colModel: [], //{display, name, width, align}
        title: "",
        buttons : [],
        init:false
    };    
    var opts = $.extend(defaults, options); */
    
    this.each(function() {  
        var vmxTab = $(this);
        $(".vmxTabList", vmxTab).click(function(){
              if(!$(this).hasClass("current")){
                    var _index = $(this).index();
                    vmxTab.data("selectedIndex", _index);
                    $(this).siblings().removeClass("current");
                    $(this).addClass("current");
                    var $vmxTabContent = $(".vmxTabBd .vmxTabContent", vmxTab);
                    $vmxTabContent.removeClass("current");
                    $vmxTabContent.eq(_index).addClass("current");
              }
        });
    });
}

$.fn.vmxTabGetSelectedIndex = function()
{
    var ret = 0;
    this.each(function() {  
        var vmxTab = $(this);
        if (typeof(vmxTab.data("selectedIndex")) != "undefined")
            ret = vmxTab.data("selectedIndex");
    });
    return ret;
}

