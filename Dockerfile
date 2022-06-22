# Setup
FROM archlinux:base-devel
RUN pacman -Syyu --needed --noconfirm --noprogressbar nodejs yarn pm2
WORKDIR /usr/src/app
COPY scripts/ scripts/
COPY ecosystem.config.js ./ecosystem.config.js
RUN ls -lah

# SWDTokenSetNotifications
RUN pacman -S --needed --noconfirm --noprogressbar python3 python-pip
WORKDIR scripts/SWDTokenSetNotifications
RUN pip install -r requirements.txt

# AutomaticTokenPriceManagerPricing
RUN pacman -S --needed --noconfirm --noprogressbar npm
WORKDIR ../AutomaticTokenPriceManagerPricing
RUN yarn && yarn build

# Process Manager
WORKDIR /usr/src/app
CMD ["pm2-runtime", "ecosystem.config.js"]
