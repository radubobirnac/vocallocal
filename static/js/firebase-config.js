// Enable offline persistence
firebase.database().setPersistence(firebase.database.Persistence.LOCAL)
  .then(() => {
    console.log("Offline persistence enabled");
  })
  .catch((error) => {
    console.error("Error enabling offline persistence:", error);
  });