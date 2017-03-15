const fs         = require('fs');
const marked     = require('marked');
const Handlebars = require('handlebars');

const env = {
  postDir : 'data/posts',
  templates : {
    post: 'template/post.hbs',
    postList: 'template/post-list.hbs',
  }
};

const readFile = function(filePath, parser) {
  const buffer = fs.readFileSync(filePath);
  return parser(buffer.toString(), filePath);
};

const readFiles = function(directoryPath, parser) {
  return fs.readdirSync(directoryPath)
    .map(fileName => `${directoryPath}/${fileName}`)
    .map(filePath => readFile(filePath, parser));
};

const postFileParser = function(file, filePath) {
  const splittedContent = file.split('---');
  const metadata = splittedContent[0];
  const content = splittedContent[1];
  const post = JSON.parse(metadata);
  post.content = marked(content);
  post.date = new Date(post.date);
  post.targetPath = filePath.replace('.md', '.html').split('/')[2];
  return post;
};

const loadTemplate = function(path) {
  const source = readFile(path, i => i);
  return Handlebars.compile(source);
};

const writePost = function(post, template, target) {
  fs.writeFileSync(target(post), template(post));
};

const posts = readFiles(env.postDir, postFileParser);
posts.sort((a, b) => b.date - a.date);
posts.map(post => writePost(post, loadTemplate(env.templates.post), post => post.targetPath));
writePost(posts[0], loadTemplate(env.templates.post), post => 'index.html');
fs.writeFileSync('list.html', loadTemplate(env.templates.postList)({ posts: posts }));
