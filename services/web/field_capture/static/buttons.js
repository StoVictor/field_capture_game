var change_username_button = document.getElementById('change-username-button');
var change_username_block = document.getElementById('change-username-block');
var close_change_username_block = document.getElementById('close-change-username-block');

var create_room_button = document.getElementById('create-room-button');
var create_room_block = document.getElementById('create-room-block');
var close_create_room_block  = document.getElementById('close-create-room-block');
var back_darkness = document.getElementById('back-darkness');

var go_to_private_room_button = document.getElementById('go-to-private-room-button');
var go_to_private_room_block = document.getElementById('go-to-private-room-block');
var close_go_to_private_room_block = document.getElementById('close-go-to-private-room-block');

var room_block_button = document.getElementById('room-block-button');
var room_block = document.getElementById('room-block');
var close_room_block = document.getElementById('close-room-block');

change_username_button.onclick = function() {
    change_username_block.style.display = "flex";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'block';
}

close_change_username_block.onclick = function() {
    change_username_block.style.display = "none";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'none';
}

create_room_button.onclick = function() {
    create_room_block.style.display = "flex";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'block';
}

close_create_room_block.onclick = function() {
    create_room_block.style.display = "none";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'none';
}


go_to_private_room_button.onclick = function() {
    go_to_private_room_block.style.display = "flex";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'block';
}

close_go_to_private_room_block.onclick = function() {
    go_to_private_room_block.style.display = "none";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'none';
}

room_block_button.onclick = function() {
    room_block.style.display = "flex";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'block';
}

close_room_block.onclick = function() {
    room_block.style.display = "none";
    document.body.style.background = "black";
    back_darkness.height = window.innerHeight;
    back_darkness.style.display = 'none';
}
