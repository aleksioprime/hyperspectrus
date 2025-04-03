import { GenerateResource } from "./generate.resource";
import { UserResource } from "./user.resource";
import { AuthResource } from "./auth.resource";
import { RequestResource } from "./request.resource";
import { CommentResource } from "./comment.resources";

export default {
    generate: new GenerateResource(),
    user: new UserResource(),
    auth: new AuthResource(),
    request: new RequestResource(),
    comment: new CommentResource(),
};