import { UserResource } from "./user.resource";
import { AuthResource } from "./auth.resource";
import { PatientResource } from "./patient.resource";
import { SessionResource } from "./session.resource";

export default {
    user: new UserResource(),
    auth: new AuthResource(),
    patient: new PatientResource(),
    session: new SessionResource(),
};