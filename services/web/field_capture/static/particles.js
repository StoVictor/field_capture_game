((c)=>{
    let $ = c.getContext('2d'),
            w = c.width = window.innerWidth,
            h = c.height = window.innerHeight,
            pi2 = Math.PI*2,
            random = t=>Math.random()*t,
            binRandom = (f)=>Math.random()<f,
            red = [255, 0 ,0],
            green = [0, 255, 0],
            blue = [0, 0, 255],
            white = [255, 255, 255],
            arr = new Array(500).fill().map((p)=>{
                return {
                    p: {x: random(w), y: random(h)},
                    v: {x: random(.5) * (binRandom(.5)?1:-1), y: random(.5) * (binRandom(.5)?1:-1)},
                    s: random(1)+2, 
                    o: random(1)+.3
                }
            });
    function draw(){
        (h !== innerHeight || w!==innerWidth) && (w=c.width=innerWidth,h=c.height=innerHeight);
        $.fillStyle="#0c0917";
        $.fillRect(0,0,w,h);
        var k = 0;
        var clr = 0;
        arr.forEach(p=>{
            p.p.x+=p.v.x;
            p.p.y+=p.v.y;
            if(p.p.x > w || p.p.x < 0) p.v.x *=-1;
            if(p.p.y > h || p.p.y < 0) p.v.y *=-1;
            $.beginPath();
            $.arc(p.p.x,p.p.y,p.s,0,pi2);
            $.closePath();
            if (k > 500) {
                k == 0
            } else if (k < 122){
                clr = "rgba("+red[0]+","+red[1]+","+red[2]+","+p.o+")"; 
            } else if (k > 122 && k < 244) {
                clr = "rgba("+blue[0]+","+blue[1]+","+blue[2]+","+p.o+")"; 
            } else if (k > 244 && k < 366) {
                clr = "rgba("+green[0]+","+green[1]+","+green[2]+","+p.o+")";
            } else {
                clr = "rgba("+white[0]+","+white[1]+","+white[2]+","+p.o+")";
            }
            k += 1;
            $.shadowColor = clr;
            $.shadowBlur = 5;
            $.fillStyle =  clr;
            $.fill();
        })
        requestAnimationFrame(draw)
    }
    draw();
})(c)
