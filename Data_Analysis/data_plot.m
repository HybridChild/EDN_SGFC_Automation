clear ;


% Load CSV files
X = csvread('log_file.csv');

temperature = X([2:end],1);
humidity = X([2:end],2);
time = [1:length(temperature)];
time = time * 2;
time = time';

figure(1)
plot(time,humidity);

ax = gca;
h0 = get(ax,'children'); % This is the handle to the plotted line
x1 = get(h0,'xdata');    % Get data for line
y1 = get(h0,'ydata');

cla(ax)                  % Clear axes
plotyy(ax,x1,y1,time,temperature);  % Plot old and new data
grid on;
%legend('Humidity', 'Temperature');
xlabel('Time [min]');
ylabel('Relative Humidity [%]');
yylabel('Temperature');
