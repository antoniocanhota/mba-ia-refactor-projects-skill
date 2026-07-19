const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const userModel = require('../models/userModel');
const paymentModel = require('../models/paymentModel');

async function buildReport(db) {
    const courses = await courseModel.findAll(db);
    const report = [];

    for (const course of courses) {
        const courseData = { course: course.title, revenue: 0, students: [] };
        const enrollments = await enrollmentModel.findByCourseId(db, course.id);

        for (const enrollment of enrollments) {
            const [user, payment] = await Promise.all([
                userModel.findById(db, enrollment.user_id),
                paymentModel.findByEnrollmentId(db, enrollment.id),
            ]);

            if (payment && payment.status === 'PAID') {
                courseData.revenue += payment.amount;
            }

            courseData.students.push({
                student: user ? user.name : 'Unknown',
                paid: payment ? payment.amount : 0,
            });
        }

        report.push(courseData);
    }

    return report;
}

module.exports = { buildReport };
