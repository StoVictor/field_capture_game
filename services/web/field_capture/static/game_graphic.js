var canv = document.getElementById('game-field');
var ctx = canv.getContext("2d");
var dice_canv = document.getElementById('dice');
var dice_ctx = dice_canv.getContext('2d');
var can_width = document.getElementById('game-field').width;
var can_height = document.getElementById('game-field').height;
var player_colors = ['#6eff76', '#b5b4b4', '#ff5d5d', '#8e8eff'];
 
// dice field

function init_dice_field() {
    dice_ctx.fillStyle = '#ffffff';
    dice_ctx.rect(0, 0, can_width, can_height);
    dice_ctx.fill();
    draw_empty_dice();
}

function draw_empty_dice() {
    dice_ctx.fillStyle = '#000000';
    dice_ctx.lineWidth = 2;
    dice_ctx.strokeRect(10, 10, 80, 80);
    dice_ctx.strokeRect(110, 10, 80, 80);
} 

function draw_init_dice(){
    draw_empty_dice();
    dice_ctx.fillStyle= '#00096e';
    draw_one_dice();
    draw_one_dice(second_dice_offset);
}

function draw_circle(x, y){
    dice_ctx.beginPath();
    dice_ctx.arc(x, y, 10, 0, 2 * Math.PI);
    dice_ctx.fill();
}
 
 
function draw_six_dice(offset_x=0){
    draw_circle(30+offset_x, 28);
    draw_circle(30+offset_x, 52);
    draw_circle(30+offset_x, 74);
    draw_circle(70+offset_x, 28);
    draw_circle(70+offset_x, 52);
    draw_circle(70+offset_x, 74);
}

function draw_five_dice(offset_x=0){
    draw_circle(30+offset_x, 28);
    draw_circle(30+offset_x, 74);
    draw_circle(50+offset_x, 52);
    draw_circle(70+offset_x, 28);
    draw_circle(70+offset_x, 74);
}

function draw_four_dice(offset_x=0) {
    draw_circle(30+offset_x, 28);
    draw_circle(30+offset_x, 74);
    draw_circle(70+offset_x, 28);
    draw_circle(70+offset_x, 74);
}
 
function draw_three_dice(offset_x=0) {
    draw_circle(30+offset_x, 28);
    draw_circle(50+offset_x, 52);
    draw_circle(70+offset_x, 74);
}
 
function draw_two_dice(offset_x=0) {
    draw_circle(30+offset_x, 52);
    draw_circle(70+offset_x, 52);
}

function draw_one_dice(offset_x=0) {
    draw_circle(50+offset_x, 52);
}

function randomInteger(min, max) {
    let rand = min + Math.random() * (max + 1 - min);
    return Math.floor(rand);
}
 
var second_dice_offset = 100;
var dice_change_interval = null;

function decide_what_dice_print(width, height, color='#00096e'){
    dice_ctx.fillStyle= color;
    switch(width){
        case 1:
            draw_one_dice();
            break;
        case 2:
            draw_two_dice();
            break;
        case 3:
            draw_three_dice();
            break;
        case 4:
            draw_four_dice();
            break;
        case 5:
            draw_five_dice();
            break;
        case 6:
            draw_six_dice();
            break;
    }
    switch(height){
        case 1:
            draw_one_dice(second_dice_offset);
            break;
        case 2:
            draw_two_dice(second_dice_offset);
            break;
        case 3:
            draw_three_dice(second_dice_offset);
            break;
        case 4:
            draw_four_dice(second_dice_offset);
            break;
        case 5:
            draw_five_dice(second_dice_offset);
            break;
        case 6:
            draw_six_dice(second_dice_offset);
            break;
    }
}

function animate_roll_dice() {
    if (dice_change_interval != null){
        clearInterval(dice_change_interval);
        dice_change_interval = null;
    }
    dice_change_interval = setInterval(function(){
        var width = randomInteger(1, 6);
        var height = randomInteger(1, 6);
        init_dice_field();
        decide_what_dice_print(width, height);
    }, 250);
}

function paint_game_field() {
    var cell_side = 25;
    ctx.fillStyle = "#ffffff";
    ctx.rect(0, 0, can_width, can_height);
    ctx.fill();
    ctx.fillStyle = 'black';
    ctx.beginPath();
    for (var i = 0; i <= can_width; i+=cell_side){
        ctx.moveTo(i, 0);
        ctx.lineTo(i, can_height);
        ctx.moveTo(0, i);
        ctx.lineTo(can_width, i);
    }
    ctx.stroke();
}

function is_it_possbile_to_create_figure(x, y, width, height, field){ 
    var z = 0;
    for (var i=0; i<width; i=i+1) {
        for (var k=0; k<height; k=k+1) {
            if (((y + k) < max_height) && 
                ((x + i) < max_width) && 
                ((y + k) >= 0) && 
                ((x + i) >= 0)) {
                if (field[y + k][x + i] == 0) {
                    z += 1;
                }
            }
        }
    }

    if (z == width*height){
        return true
    }

    return false 
}

function make_figure(x, y, width, height, color, field, force=false) {
   var grid_offset = 1;
   var cell_side = 25;
   ctx.fillStyle = color;
   max_height = field.length;
   max_width = field[0].length;
   cell_y = Math.round(y / cell_side);
   cell_x = Math.round(x / cell_side);
   for (var i=0; i<width; i=i+1) {
       for (var k=0; k<height; k=k+1) {
           if (!force) {
                if (((cell_y + k) < max_height) && 
                    ((cell_x + i) < max_width) && 
                    ((cell_y + k) >= 0) && 
                    ((cell_x + i) >= 0)) {
                    if (field[cell_y + k][cell_x + i] == 0) {
                        ctx.fillRect((x+1)+(cell_side*i), (y+1)+(cell_side*k),
                                     cell_side-2*grid_offset, cell_side-2*grid_offset);
                    }
                }
           } else {
                ctx.fillRect((x+grid_offset) + (cell_side*i), (y+grid_offset) + (cell_side*k),
                             cell_side-2*grid_offset, cell_side-2*grid_offset);
           }
       }
   }
}

function build_field_from_data(field) {
    var cell_side = 25;
    var grid_offset = 1;

    for (var i=0; i<field[0].length; i++) {
        for (var k=0; k<field.length; k++) {
            ctx.fillStyle = figure_colors[field[k][i]];
            ctx.fillRect(grid_offset + (cell_side*i), grid_offset + (cell_side*k),
                         cell_side-2*grid_offset, cell_side-2*grid_offset);
        }
    }
}
