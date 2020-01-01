var starsNumber = 100;

var c = document.getElementById('c');
var ctx_back = c.getContext('2d');

var w = window.innerWidth;
var h = window.innerHeight;
var x = 100; var y = 100;

var stars = [];

var pi2 = Math.PI * 2;
var quarters = [starsNumber*0.25, starsNumber*0.5, starsNumber*0.75];

for(i = 0; i < starsNumber; i++) {
  stars.push(new star);
};

function star() {
  this.x = Math.random() * w;
  this.y = Math.random() * h;
  
  this.vx = 1;
  
  this.r = Math.random(1) + 2;
}

function draw() {
	c.width = w;
	c.height = h;
  
  for(t = 0; t < stars.length; t++) {
    var s = stars[t];
    
    ctx_back.beginPath();
    if (t < quarters[0]){
        ctx_back.fillStyle = "#ff0000";
        ctx_back.shadowColor = "#ff0000";
        ctx_back.shadowBlur = 4;
    } else if ((quarters[0] <= t )&& (t < quarters[1])){
        ctx_back.fillStyle = "#00ff00";
        ctx_back.shadowColor = "#00ff00";
        ctx_back.shadowBlur = 4
    } else if((quarters[1] <= t) && (t < quarters[2])){
        ctx_back.fillStyle = "#0000ff";
        ctx_back.shadowColor = "#0000ff";
        ctx_back.shadowBlur = 4;
    } else {
        ctx_back.fillStyle = "#ffffff";
        ctx_back.shadowColor = "#ffffff";
        ctx_back.shadowBlur = 4;
    }
  	
  	ctx_back.arc(s.x, s.y, s.r, pi2, false);
  	ctx_back.fill();
    
    s.x-=s.vx;
    
    if(s.x < -s.r) {
      s.x = w + s.r;
    };
    if(s.r < 5) {
      s.vx = 1;
    };
    if(s.r < 4) {
      s.vx = 0.5;
    };
    if(s.r < 3) {
      s.vx = 0.25;
    };
  }
}

setInterval(draw, 50);
