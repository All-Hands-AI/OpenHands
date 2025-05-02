const { GitService } = require('./git-service');

async function testGitService() {
    const gitService = new GitService();
    
    try {
        console.log('Getting changes...');
        const changes = await gitService.getChanges();
        console.log('Changes:', changes);
        
        if (changes.length > 0) {
            const firstChange = changes[0];
            console.log(`Getting diff for ${firstChange.path}...`);
            const diff = await gitService.getDiff(firstChange.path);
            console.log('Diff:', diff);
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

testGitService();