

/**************************************************************

	Script		: Sortable Table
	Version		: 1.4
	Authors		: Samuel Birch
	Desc			: Sorts and filters table elements
	Licence		: Open Source MIT Licence

**************************************************************/

var counter=0;
var sortableTable=new Class(
{
getOptions:function()
  {
  return{overCls:false,onClick:false,sortOn:0,sortBy:"ASC",filterHide:true,filterHideCls:"hide",filterSelectedCls:"selected"}
  },

initialize:function(b,a)
  {
  this.setOptions(this.getOptions(),a);

  this.table=$(b);
  this.tHead=this.table.getElement("thead");
  this.tBody=this.table.getElement("tbody");
  this.tFoot=this.table.getElement("tfoot");
  this.elements=this.tBody.getElements("tr");
  this.filtered=false;

  this.tHead.getElements("th").each(function(d,c)
    {
    if(d.axis)
      {
      d.addEvent("click",this.sort.bind(this,c));
      d.addEvent("mouseover",function(){d.addClass("tableHeaderOver")});
      d.addEvent("mouseout",function(){d.removeClass("tableHeaderOver")});
      d.getdate=function(g)
        {function f(h)
          {
          h=+h;
          if(h<50)
            {
            h+=2000
            }
          else
            {
            if(h<100)
              {
              h+=1900
              }
            }
          return h
          }
        var e;
        if(g.length>12)
          {
          strtime=g.substring(g.lastIndexOf(" ")+1);
          strtime=strtime.substring(0,2)+strtime.substr(-2)
          }
        else
          {
          strtime="0000"
          }
        if(e=g.match(/(\d{2,4})-(\d{1,2})-(\d{1,2})/))
          {
          return(f(e[1])*10000)+(e[2]*100)+(+e[3])+strtime
          }
        if(e=g.match(/(\d{1,2})[\/-](\d{1,2})[\/-](\d{2,4})/))
          {
          return(f(e[3])*10000)+(e[2]*100)+(+e[1])+strtime
          }
          return 999999990000
        };
    d.findData=function(e)
      {
      var f=e.getFirst();
      if(f){return d.findData(f)}else{return e.innerHTML.trim()}
      };
    d.compare=function(f,e)
      {
      var1=d.findData(f.getChildren()[c]);
      var2=d.findData(e.getChildren()[c]);
      if(d.axis=="number")
        {
        var1=parseFloat(var1);
        var2=parseFloat(var2);
        if(d.sortBy=="ASC")
          {
          return var1-var2
          }
        else
          {
          return var2-var1
          }
        }
      else
        {
        if(d.axis=="string")
          {
          var1=var1.toUpperCase();
          var2=var2.toUpperCase();
          if(var1==var2){return 0}if(d.sortBy=="ASC"){if(var1<var2){return -1}}else{if(var1>var2){return -1}}return 1
          }
        else
          {
          if(d.axis=="date")
            {
            var1=parseFloat(d.getdate(var1));
            var2=parseFloat(d.getdate(var2));
            if(d.sortBy=="ASC"){return var1-var2}else{return var2-var1}
            }
          else
            {
            if(d.axis=="currency")
              {
              var1=parseFloat(var1.substr(1).replace(",",""));
              var2=parseFloat(var2.substr(1).replace(",",""));
              if(d.sortBy=="ASC"){return var1-var2}else{return var2-var1}
              }
            else
              {
              if(d.axis=="custom")
                {
                var1=var1.toUpperCase();var2=var2.toUpperCase();
                if(var1=="-")
                  {var1="FO 00.00.0000 00:00"}
                if(var2=="-")
                  {var2="FO 00.00.0000 00:00"}
                var h=new Array();
                h=var1.split(".");
				
                var1=h[2].substring(0,4)+h[1]+h[0].replace(/\D/g,"")+h[2].substring(5,7)+h[2].substring(8,10);
                var g=new Array();
                g=var2.split(".");
                var2=g[2].substring(0,4)+g[1]+g[0].replace(/\D/g,"")+g[2].substring(5,7)+g[2].substring(8,10);
                if(var1==var2){return 0}
                if(d.sortBy=="ASC")
                  {if(var1<var2){return -1}}
                else
                  {if(var1>var2){return -1}}
                return 1
                }
              }
            }
          }
        }
      };

if(c==this.options.sortOn){d.click()}
      }
}
,this)
  },

sort:function(c, dir)
  {
  if(this.options.onStart)
    {
    this.fireEvent("onStart")
    }
    
  this.options.sortOn=c;
  var h=this.tHead.getElements("th");
  var f=h[c];
  h.each(function(k,j)
    {
    if(j!=c)
      {
      k.removeClass("sortedASC");
      k.removeClass("sortedDESC")
      }
    }
  );

//---
  if( dir == undefined )
    dir = '';
  else if( dir == 'ASC' )
    {
    this.options.sortBy="ASC";
    f.removeClass("sortedASC");
    f.removeClass("sortedDESC");
    }
  else if( dir == 'DESC' )
    {
    this.options.sortBy="DESC";
    f.removeClass("sortedASC");
    f.removeClass("sortedDESC");
    }
//---

  if(f.hasClass("sortedASC"))
    {
    f.removeClass("sortedASC");
    f.addClass("sortedDESC");
    f.sortBy="DESC"
    }
  else
    {
    if(f.hasClass("sortedDESC"))
      {
      f.removeClass("sortedDESC");
      f.addClass("sortedASC");
      f.sortBy="ASC"
      }
    else
      {
      if(this.options.sortBy=="ASC")
        {
        f.addClass("sortedASC");
        f.sortBy="ASC"
        }
      else
        {
        if(this.options.sortBy=="DESC")
          {
          f.addClass("sortedDESC");
          f.sortBy="DESC"
          }
        }
      }
    }
  this.elements.sort(f.compare);
  this.elements.injectInside(this.tBody);
  if(this.filtered)
    {
    this.filteredAltRow()
    }
  else
    {
    this.altRow()
    }
  if(this.options.onComplete)
    {
    this.fireEvent("onComplete")
    }
  if(counter!=0)
    {
    var b="data/sorting.txt";
    var g=new ActiveXObject("Scripting.FileSystemObject");
    var d=g.CreateTextFile(b,true);
    var e=c;
    var a=f.sortBy;
    d.writeline(e+"\r\n"+a+"\r\n");d.close()
    }
  counter++
  },
  
  
altRow:function()
  {
  this.elements.each(function(b,a)
    {
    if(a%2)
      {
      b.removeClass("altRow")
      }
    else
      {
      b.addClass("altRow")
      }
    })
  },


filteredAltRow:function(){this.table.getElements("."+this.options.filterSelectedCls).each(function(b,a){if(a%2){b.removeClass("altRow")}else{b.addClass("altRow")}})},


filter:function(c)
  {
  var c=$(c);
  var a=0;
  var b="";
  c.getChildren().each(function(e,d)
    {
    if(e.id=="column")
      {
      a=Number(e.value)
      }
    if(e.id=="keyword")
      {
      b=e.value.toLowerCase()
      }
    if(e.type=="reset")
      {
      e.addEvent("click",this.clearFilter.bind(this))
      }
    },this);
  if(b)
    {
    this.elements.each(function(e,d){if(this.options.filterHide){e.removeClass("altRow")}if(e.getChildren()[a].firstChild.data.toLowerCase().indexOf(b)>-1){e.addClass(this.options.filterSelectedCls);if(this.options.filterHide){e.removeClass(this.options.filterHideCls)}}else{e.removeClass(this.options.filterSelectedCls);if(this.options.filterHide){e.addClass(this.options.filterHideCls)}}},this);if(this.options.filterHide){this.filteredAltRow();this.filtered=true}
    }
  },


clearFilter:function()
  {
  this.elements.each(function(b,a)
    {
    b.removeClass(this.options.filterSelectedCls);
    if(this.options.filterHide){b.removeClass(this.options.filterHideCls)}},this);if(this.options.filterHide){this.altRow();this.filtered=false}
  }
    
    
} );  // end of class

sortableTable.implement(new Events);
sortableTable.implement(new Options);