clc
clear
close all


byte2float = @(b) typecast(fliplr(uint8(b)), 'single');
data_val_size = 4

% filePath = './data/L4_20230208_112704.dat';
% filePath = './data/L4_20230208_112755.dat'
% filePath = './data/L4_20230208_112920.dat'
% filePath = './data/L4_20230208_113141.dat'
% filePath = './data/L4_20230208_125925.dat'
% filePath = './data/L4_20230208_130041.dat'
% filePath = './data/L4_20230208_134908.dat'
% filePath = './data/L4_20230208_134954.dat'
% filePath = './data/L4_20230208_135138.dat'
% filePath = './data/L4_20230208_135256.dat'
filePath = './data/L4_20230208_140250.dat'
% filePath = './data/L4_20230208_110405.dat'
% filePath = './data/L4_20230208_110405.dat'


fileId = fopen(filePath, 'rb', 'l');
raw_data = fread(fileId);
fclose(fileId);

headerTag = ['DE'; 'AD'; 'BE'; 'EF']
headerTagBytes = hex2dec(headerTag)';
m = strfind(raw_data', headerTagBytes);
header_end = m(end)+numel(headerTagBytes)-1;
header_idx = 1:header_end;

header_bytes = raw_data(header_idx);
header_char = dec2hex(header_bytes);
header_field_bytes = header_bytes(5:end-4);
chan_ct_bytes = header_field_bytes(1:2);
num_channels = typecast(uint8(chan_ct_bytes), 'uint16');
num_channels = double(num_channels);
% num_channels = 1;
data_speed_bytes = header_field_bytes(3:end)
% dec2hex(data_speed_bytes);
data_speed = typecast(fliplr(uint8(data_speed_bytes)), 'uint16')
data_bytes = raw_data(header_end+1:end);


% raw_data_char_prev = dec2hex(raw_data(1:32))
% data_bytes_char = dec2hex(data_bytes);
% tmp = data_bytes_char(1:16,:)
% tmp2 = hex2dec(tmp)



data_bytes = swapByteOrder(data_bytes);
data_bytes_rs = reshape(data_bytes', data_val_size, [])';
% data_bytes_rs = reshape(data_bytes_rs_1, 4, [])';
data_size_raw = size(data_bytes_rs);
chan_data_size = floor(data_size_raw(1)/num_channels)
data_size = prod(chan_data_size*num_channels);
data_bytes_keep = data_bytes_rs(1:data_size, :)

% chanData = cell(chan_data_size)
chanFloatData = zeros(chan_data_size);
for ii=0:num_channels-1
    row_idx = (1+ii):num_channels:data_size(1);
    tmp = data_bytes_keep(row_idx, :);
    chanData = data_bytes_keep(row_idx, :);
    chanDataCell = mat2cell(chanData, ones(1, chan_data_size(1)), data_val_size);
    chanFloatData(:,ii+1) = cellfun(byte2float, chanDataCell);
end

% data_points = data_size(1);
% data_cell = mat2cell(data_bytes_keep, ones(1, data_points), data_val_size)
% floatData = cellfun(byte2float, data_cell);

f99 = figure(99);
f99.Position = [1995 902 1891 420];
dt = 1.0/double(data_speed);
time = (0:chan_data_size(1)-1)*dt;
for ii=1:num_channels
    plot(time, chanFloatData(:,ii), '.-')
    hold on;
end
title([num2str(data_speed) 'Hz'])


function data_out = swapByteOrder(data_in)
%     tmp = dec2hex(data_in(1:16))
    data_bytes_tmp = reshape(data_in, 2, [])';
    data_bytes_tmp = fliplr(data_bytes_tmp);
    data_out = reshape(data_bytes_tmp', 4, [])';
    tmp = data_out(:,1:2);
    data_out(:,1:2) = data_out(:,3:4);
    data_out(:,3:4) = tmp;
end
