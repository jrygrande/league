// Quick API test script to verify our setup works
const axios = require('axios');

async function testAPI() {
  try {
    console.log('🧪 Testing API endpoints...\n');

    // Test 1: Basic connectivity
    console.log('1. Testing basic connectivity...');
    const health = await axios.get('http://localhost:8000/');
    console.log('✅ Health check:', health.data);

    // Test 2: User endpoint
    console.log('\n2. Testing user endpoint...');
    try {
      const user = await axios.get('http://localhost:8000/user/testuser');
      console.log('✅ User data:', {
        username: user.data.username,
        user_id: user.data.user_id,
        display_name: user.data.display_name
      });
    } catch (err) {
      console.log('❌ User test failed:', err.response?.data || err.message);
    }

    // Test 3: Players endpoint (just check structure)
    console.log('\n3. Testing players endpoint...');
    try {
      const players = await axios.get('http://localhost:8000/players');
      const playerIds = Object.keys(players.data);
      const firstPlayer = players.data[playerIds[0]];
      console.log('✅ Players endpoint working. Sample player:', {
        total_players: playerIds.length,
        sample: {
          player_id: firstPlayer.player_id,
          name: firstPlayer.full_name,
          position: firstPlayer.position,
          team: firstPlayer.team
        }
      });
    } catch (err) {
      console.log('❌ Players test failed:', err.response?.data || err.message);
    }

    console.log('\n🎉 API tests completed!');
  } catch (error) {
    console.log('❌ Connection failed:', error.message);
    console.log('Make sure the backend is running on http://localhost:8000');
  }
}

testAPI();