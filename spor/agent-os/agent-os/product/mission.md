# Product Mission

## Problem

Gjøremål uten struktur blir en eneste lang haug. Man trenger å skille
arbeid fra handleliste fra ferieplanlegging, og å flytte et gjøremål over
når det viser seg å høre hjemme et annet sted.

## Target Users

Klienter som snakker HTTP — en frontend, et skript, en annen tjeneste.
Produktet er et API, ikke et grensesnitt. Det finnes ingen innlogging og
ingen brukere; alle deler samme data.

## Solution

Et lite, forutsigbart REST-API over to ressurser: lister og gjøremål.

- Hvert gjøremål hører hjemme i nøyaktig én liste, håndhevet av databasen.
- Å flytte et gjøremål er en vanlig endring av hvilken liste det peker på,
  ikke en egen mekanisme.
- Oppslag på noe som ikke finnes er et normalt svar (404 med forklaring),
  ikke en feil som velter applikasjonen.
- Data ligger i SQLite på disk og overlever omstart.
