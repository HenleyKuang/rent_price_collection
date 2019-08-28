python rent_price_collection/api/rent_price_collection_api.py &
cd rent_price_collection/ui
echo "Reinstalling Node Packages..."
npm install
echo "Starting React UI..."
npm start

read -p "Press enter to continue"